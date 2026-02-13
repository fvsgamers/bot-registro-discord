import discord
from discord.ext import commands
from config import (
    CARGOS,
    CARGO_APROVADOR_ID,
    CATEGORIA_REGISTROS_ID,
    PRIORIDADE_NICK,
    REMOVER_CARGOS_APOS_APROVACAO,
    CARGO_FIXO_APOS_APROVACAO
)
import os
import asyncio

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise Exception("TOKEN não configurado nas variáveis de ambiente da Koyeb!")

CANAL_PAINEL_ID = 1459275771301593353

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# ================= MODAL ==============================
# ======================================================

class RegistroModal(discord.ui.Modal, title="📋 Solicitação de Registro"):

    nome = discord.ui.TextInput(label="Nome", max_length=30)
    sobrenome = discord.ui.TextInput(label="Sobrenome", max_length=30)

    def __init__(self, cargos):
        super().__init__()
        self.cargos = cargos

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild
        categoria = guild.get_channel(CATEGORIA_REGISTROS_ID)

        if not categoria:
            return await interaction.response.send_message(
                "❌ Categoria de registros não encontrada.",
                ephemeral=True
            )

        aprovador_role = guild.get_role(CARGO_APROVADOR_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            aprovador_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            name=f"registro-{interaction.user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        view = AprovacaoView(
            interaction.user.id,
            self.nome.value.strip(),
            self.sobrenome.value.strip(),
            self.cargos,
            canal.id
        )

        cargos_texto = ", ".join([CARGOS[c]["nome"] for c in self.cargos])

        await canal.send(
            f"📥 **Novo Pedido de Registro**\n\n"
            f"👤 Usuário: {interaction.user.mention}\n"
            f"📛 Nome: {self.nome.value} {self.sobrenome.value}\n"
            f"🎖 Cargos Selecionados: {cargos_texto}",
            view=view
        )

        await interaction.response.send_message(
            "✅ Pedido enviado para aprovação.",
            ephemeral=True
        )

# ======================================================
# ================= SELECT =============================
# ======================================================

class CargoSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(
                label=CARGOS[key]["nome"],
                value=key
            )
            for key in CARGOS
        ]

        super().__init__(
            placeholder="Selecione seus cargos",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistroModal(self.values))


class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CargoSelect())

# ======================================================
# ================= APROVAÇÃO ==========================
# ======================================================

class AprovacaoView(discord.ui.View):
    def __init__(self, membro_id, nome, sobrenome, cargos, canal_id):
        super().__init__(timeout=None)
        self.membro_id = membro_id
        self.nome = nome
        self.sobrenome = sobrenome
        self.cargos = cargos
        self.canal_id = canal_id

    async def interaction_check(self, interaction: discord.Interaction):
        if CARGO_APROVADOR_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ Você não tem permissão para aprovar.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button):

        guild = interaction.guild
        membro = guild.get_member(self.membro_id)

        if not membro:
            return await interaction.response.send_message(
                "❌ Membro não encontrado.",
                ephemeral=True
            )

        # 1️⃣ Remover cargos definidos
        for cargo_id in REMOVER_CARGOS_APOS_APROVACAO:
            role = guild.get_role(cargo_id)
            if role and role in membro.roles:
                await membro.remove_roles(role)

        # 2️⃣ Adicionar cargo fixo
        cargo_fixo = guild.get_role(CARGO_FIXO_APOS_APROVACAO)
        if cargo_fixo:
            await membro.add_roles(cargo_fixo)

        # 3️⃣ Remover cargos do sistema antes de setar
        for c in CARGOS.values():
            role = guild.get_role(c["id"])
            if role and role in membro.roles:
                await membro.remove_roles(role)

        # 4️⃣ Adicionar cargos selecionados
        for key in self.cargos:
            cargo_info = CARGOS[key]
            role = guild.get_role(cargo_info["id"])
            if role:
                await membro.add_roles(role)

        # 5️⃣ Aplicar prioridade no nickname
        cargo_nick = None
        for prioridade in PRIORIDADE_NICK:
            if prioridade in self.cargos:
                cargo_nick = CARGOS[prioridade]
                break

        if cargo_nick and cargo_nick["prefixo"]:
            novo_nick = f"{cargo_nick['prefixo']} {self.nome} {self.sobrenome}"
        else:
            novo_nick = f"{self.nome} {self.sobrenome}"

        try:
            await membro.edit(nick=novo_nick)
        except discord.Forbidden:
            pass

        await interaction.response.edit_message(
            content="✅ Registro aprovado com sucesso.",
            view=None
        )

        await asyncio.sleep(3)

        canal = guild.get_channel(self.canal_id)
        if canal:
            await canal.delete()

    @discord.ui.button(label="❌ Rejeitar", style=discord.ButtonStyle.danger)
    async def rejeitar(self, interaction: discord.Interaction, button):
        await interaction.response.edit_message(
            content="❌ Registro rejeitado.",
            view=None
        )

# ======================================================
# ================= COMANDO ============================
# ======================================================

@bot.command()
async def painel(ctx):

    if ctx.channel.id != CANAL_PAINEL_ID:
        return await ctx.send("❌ Use este comando no canal correto.")

    async for msg in ctx.channel.history(limit=15):
        if msg.author == bot.user and msg.components:
            return await ctx.send("❌ O painel já existe neste canal.")

    await ctx.send(
        "📋 **Painel de Registro**\nSelecione seus cargos abaixo:",
        view=RegistroView()
    )

# ======================================================
# ================= ONLINE =============================
# ======================================================

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")
    bot.add_view(RegistroView())

bot.run(TOKEN)
