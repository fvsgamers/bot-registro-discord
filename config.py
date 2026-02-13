# =========================
# CONFIG SISTEMA REGISTRO
# =========================

CARGOS = {
    "staff": {
        "nome": "🛡️ Staff",
        "id": 1459264090105970696,
        "prefixo": "[STAFF]"
    },
    "mod": {
        "nome": "⚙️ MOD",
        "id": 1471731349374242990,
        "prefixo": "[MOD]"
    },
    "vip": {
        "nome": "💎 VIP",
        "id": 1459264090105970694,
        "prefixo": "[VIP]"
    },
    "streamer": {
        "nome": "🎮 Streamer",
        "id": 1459264090105970695,
        "prefixo": ""
    },
    "membro": {
        "nome": "👤 Membro",
        "id": 1459264090105970693,
        "prefixo": "[MEMBRO]"
    },
    "visitante": {
        "nome": "🏞 Visitante",
        "id": 1459264089762304115,
        "prefixo": ""
    }
}

# Cargo que pode aprovar
CARGO_APROVADOR_ID = 1459264090105970696

# Categoria onde os canais serão criados
CATEGORIA_REGISTROS_ID = 1471732973467468008

# Prioridade do prefixo do nickname
PRIORIDADE_NICK = ["staff", "mod", "vip", "membro"]

# =========================
# CARGOS FIXOS DO SISTEMA
# =========================

REMOVER_CARGOS_APOS_APROVACAO = [
    1459264089762304115,  # visitante
    1471729781635813503
]

CARGO_FIXO_APOS_APROVACAO = 1471729614455046307
