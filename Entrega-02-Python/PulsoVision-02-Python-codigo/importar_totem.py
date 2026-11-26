# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/importar_totem.py
# Resumo:  Integração com o AICSS: lê as leituras reais gravadas pelo totem
#          (cópia em dados_totem/dados.csv) e envia cada uma para a API
#          por HTTP.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:5000/leituras"
ORIGEM_PADRAO = Path(__file__).resolve().parent / "dados_totem" / "dados.csv"

INTEIROS = {"id_leitura", "pessoas_aguardando"}
DECIMAIS = {"fila_distancia_cm"}
BOOLEANOS = {"movimento"}


def para_contrato(linha):
    leitura = {k: v for k, v in linha.items() if k != "data_hora"}
    for campo in INTEIROS:
        leitura[campo] = int(leitura[campo])
    for campo in DECIMAIS:
        leitura[campo] = float(leitura[campo])
    for campo in BOOLEANOS:
        leitura[campo] = leitura[campo].lower() == "true"
    return leitura


def enviar(leitura):
    pedido = urllib.request.Request(API, data=json.dumps(leitura).encode("utf-8"), method="POST",
                                    headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code


def main():
    origem = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGEM_PADRAO
    if not origem.exists():
        print(f"Arquivo não encontrado: {origem}")
        return
    with origem.open(newline="", encoding="utf-8") as arquivo:
        linhas = [l for l in csv.DictReader(arquivo) if l["id_totem"].startswith("TOTEM-")]

    resultado = {}
    for linha in linhas:
        codigo = enviar(para_contrato(linha))
        resultado[codigo] = resultado.get(codigo, 0) + 1

    print(f"Leituras reais do totem lidas de {origem.name}: {len(linhas)}")
    print(f"Respostas da API: {resultado}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError:
        print("A API não está rodando em", API)
