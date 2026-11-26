# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/cenarios.py
# Resumo:  Demonstração dos três cenários de teste contra a API rodando:
#          mostra cada requisição e a resposta e, no fim, a consulta GET e os
#          indicadores.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import json
import urllib.error
import urllib.request

API = "http://127.0.0.1:5000"

BASE = {
    "versao_contrato": "1.0",
    "id_totem": "SIMULADOR-01",
    "cnes": "4048296",
    "nome_unidade": "UBS Jardim Paulista",
    "tipo_unidade": "UBS",
    "cod_municipio": "351880",
}

CENARIOS = [
    ("Cenário 1 · Fila curta: a API grava e recomenda a unidade", {
        **BASE, "id_leitura": 1, "fila_distancia_cm": 403.5, "fila_status": "CURTA", "movimento": True,
        "movimento_status": "FLUXO", "pessoas_aguardando": 0, "status": "OK", "motivo": "FILA_CURTA"}),
    ("Cenário 2 · Fila parada: a API marca LOTADO e indica outra unidade", {
        **BASE, "id_leitura": 2, "fila_distancia_cm": 200.0, "fila_status": "MEDIA", "movimento": False,
        "movimento_status": "SEM_FLUXO", "pessoas_aguardando": 3, "status": "LOTADO", "motivo": "FILA_PARADA"}),
    ("Cenário 3 · Leitura inválida: a API recusa e não grava", {
        **BASE, "id_leitura": 3, "fila_distancia_cm": 200.0, "fila_status": "MEDIA", "movimento": False,
        "movimento_status": "SEM_FLUXO", "pessoas_aguardando": "muitas", "motivo": "FILA_PARADA"}),
]


def requisitar(metodo, rota, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    pedido = urllib.request.Request(API + rota, data=dados, method=metodo,
                                    headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status, json.loads(resposta.read())
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read())


def mostrar(titulo, metodo, rota, corpo=None):
    print("=" * 78)
    print(titulo)
    print(f"{metodo} {rota}")
    if corpo is not None:
        print("Requisição:", json.dumps(corpo, ensure_ascii=False))
    codigo, resposta = requisitar(metodo, rota, corpo)
    print(f"Resposta {codigo}:")
    print(json.dumps(resposta, indent=2, ensure_ascii=False))
    return resposta


def main():
    for titulo, corpo in CENARIOS:
        mostrar(titulo, "POST", "/leituras", corpo)

    mostrar("Consulta · últimas leituras gravadas", "GET", "/leituras?limite=3")
    mostrar("Indicador · lotação por unidade", "GET", "/indicadores")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError:
        print("A API não está rodando em", API)
