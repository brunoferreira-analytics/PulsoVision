# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/models/leitura.py
# Resumo:  Contrato JSON v1.0 compartilhado com o totem (AICSS): campos,
#          tipos, valores permitidos e faixas, e a função que valida cada
#          leitura recebida.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

CONTRATO = {
    "versao_contrato": str,
    "id_leitura": int,
    "id_totem": str,
    "cnes": str,
    "nome_unidade": str,
    "tipo_unidade": str,
    "cod_municipio": str,
    "fila_distancia_cm": float,
    "fila_status": str,
    "movimento": bool,
    "movimento_status": str,
    "pessoas_aguardando": int,
    "status": str,
    "motivo": str,
}

VALORES_PERMITIDOS = {
    "versao_contrato": {"1.0"},
    "tipo_unidade": {"UBS", "UPA", "PA", "HOSPITAL"},
    "fila_status": {"CURTA", "MEDIA", "LONGA", "SEM_LEITURA"},
    "movimento_status": {"FLUXO", "SEM_FLUXO"},
    "status": {"OK", "ALERTA", "LOTADO", "SEM_LEITURA"},
    "motivo": {"FILA_CURTA", "FILA_MEDIA", "FILA_PARADA", "FILA_LONGA", "SENSOR_SEM_ECO"},
}

FAIXAS = {
    "id_leitura": (1, 10_000_000),
    "fila_distancia_cm": (0.0, 500.0),
    "pessoas_aguardando": (0, 50),
}


def tipo_correto(valor, tipo):
    if tipo is bool:
        return isinstance(valor, bool)
    if tipo is int:
        return isinstance(valor, int) and not isinstance(valor, bool)
    if tipo is float:
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    return isinstance(valor, tipo)


def validar(leitura):
    if not isinstance(leitura, dict):
        return ["a leitura deve ser um objeto JSON {...}"]

    erros = []
    for campo, tipo in CONTRATO.items():
        if campo not in leitura:
            erros.append(f"campo ausente: {campo}")
        elif not tipo_correto(leitura[campo], tipo):
            erros.append(f"tipo inválido em {campo}")

    for campo in leitura:
        if campo not in CONTRATO:
            erros.append(f"campo fora do contrato: {campo}")

    if erros:
        return erros

    for campo, permitidos in VALORES_PERMITIDOS.items():
        if leitura[campo] not in permitidos:
            erros.append(f"valor não permitido em {campo}: {leitura[campo]}")

    for campo, (minimo, maximo) in FAIXAS.items():
        if not minimo <= leitura[campo] <= maximo:
            erros.append(f"{campo} fora da faixa [{minimo}, {maximo}]")

    if not (leitura["cnes"].isdigit() and len(leitura["cnes"]) == 7):
        erros.append("cnes deve ter 7 dígitos")
    if not (leitura["cod_municipio"].isdigit() and len(leitura["cod_municipio"]) == 6):
        erros.append("cod_municipio deve ter 6 dígitos")

    return erros
