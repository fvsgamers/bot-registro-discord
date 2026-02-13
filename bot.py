import discord
from discord.ext import commands
from config import CARGOS, CARGO_APROVADOR_ID, CATEGORIA_REGISTROS_ID, PRIORIDADE_NICK
import os

# ================= CONFIG ================= #

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise Exception("TOKEN não configurado nas variáveis de ambiente da Koyeb!")

CANAL_PAINEL_ID = 1459275771301593353

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= MODAL ================= #

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

        cargos_texto = ", ".join([CARGOS[c]["nome"] for c in self.cargos])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(CARGO_APROVADOR_ID): discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            name=f"registro-{interaction.user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        view = AprovacaoView(
            interaction.user.id,
            self.nome.value,
            self.sobrenome.value,
            self.cargos
        )

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

# ================= SELECT ================= #

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
            placeholder="Selecione os cargos",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            RegistroModal(self.values)
        )

class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CargoSelect())

# ================= APROVAÇÃO ================= #

class AprovacaoView(discord.ui.View):
    def __init__(self, membro_id, nome, sobrenome, cargos):
        super().__init__(timeout=None)
        self.membro_id = membro_id
        self.nome = nome
        self.sobrenome = sobrenome
        self.cargos = cargos

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
            return

        # Remove cargos antigos
        for c in CARGOS.values():
            role = guild.get_role(c["id"])
            if role and role in membro.roles:
                await membro.remove_roles(role)

        # Adiciona cargos selecionados
        for key in self.cargos:
            cargo_info = CARGOS[key]
            role = guild.get_role(cargo_info["id"])
            if role:
                await membro.add_roles(role)

        # -------- PRIORIDADE DO NICK -------- #

        cargo_nick = None

        for prioridade in PRIORIDADE_NICK:
            if prioridade in self.cargos:
                cargo_nick = CARGOS[prioridade]
                break

        if cargo_nick and cargo_nick["prefixo"] != "":
            novo_nick = f"{cargo_nick['prefixo']} {self.nome} {self.sobrenome}"
        else:
            novo_nick = f"{self.nome} {self.sobrenome}"

        try:
            await membro.edit(nick=novo_nick)
        except:
            pass

        await interaction.response.edit_message(
            content="✅ Registro aprovado com sucesso.",
            view=None
        )

    @discord.ui.button(label="❌ Rejeitar", style=discord.ButtonStyle.danger)
    async def rejeitar(self, interaction: discord.Interaction, button):
        await interaction.response.edit_message(
            content="❌ Registro rejeitado.",
            view=None
        )

# ================= COMANDO ================= #

@bot.command()
async def painel(ctx):

    if ctx.channel.id != CANAL_PAINEL_ID:
        await ctx.send("❌ Este comando só pode ser usado no canal de registro.")
        return

    await ctx.send(
        "📋 **Painel de Registro**\nSelecione seus cargos abaixo:",
        view=RegistroView()
    )

# ================= ONLINE ================= #

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")
    bot.add_view(RegistroView())

# ================= START ================= #
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

bot.run(TOKEN)
