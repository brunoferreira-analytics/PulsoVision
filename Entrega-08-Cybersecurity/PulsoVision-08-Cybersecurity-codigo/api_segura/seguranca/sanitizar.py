# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/seguranca/sanitizar.py
# Resumo:  Neutraliza CSV/formula injection antes de gravar o histórico.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

PERIGOSOS = ("=", "+", "-", "@", "\t", "\r")


def neutralizar_csv(valor):
    """Evita CSV/formula injection: texto que começa com = + - @ vira texto puro quando o CSV é aberto no Excel."""
    if isinstance(valor, str) and valor.startswith(PERIGOSOS):
        return "'" + valor
    return valor


def neutralizar_registro(registro):
    return {campo: neutralizar_csv(valor) for campo, valor in registro.items()}
