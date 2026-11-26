# PulsoVision · Totem de Lotação
# Disciplina 01: AI Computer Systems & Sensors (AICSS) · Global Solution 2026.2 — FIAP
#
# Arquivo: 01-aicss-totem/server_socket/servidor.py
# Resumo:  Servidor externo que recebe as leituras do ESP32 por socket TCP
#          (porta 5000), valida o JSON contra o contrato v1.0, exibe a
#          leitura, grava em dados.csv e registra as mensagens recusadas
#          em rejeitados.log sem sair do ar.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import csv
import json
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

HOST = "0.0.0.0"
PORT = 5000
PASTA = Path(__file__).resolve().parent
CSV_FILE = PASTA / "dados.csv"
LOG_REJEITADOS = PASTA / "rejeitados.log"

TAMANHO_MAXIMO_BYTES = 4096
TIMEOUT_CONEXAO_S = 5

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

CSV_FIELDS = ["data_hora"] + list(CONTRATO)

contagem_status = Counter()
total_rejeitadas = 0


def tipo_correto(valor, tipo):
    if tipo is bool:
        return isinstance(valor, bool)
    if tipo is int:
        return isinstance(valor, int) and not isinstance(valor, bool)
    if tipo is float:
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    return isinstance(valor, tipo)


def validar(payload):
    if not isinstance(payload, dict):
        return ["a mensagem não é um objeto JSON {...}"]

    erros = []
    for campo, tipo in CONTRATO.items():
        if campo not in payload:
            erros.append(f"campo ausente: {campo}")
        elif not tipo_correto(payload[campo], tipo):
            erros.append(f"tipo inválido em {campo}: {type(payload[campo]).__name__}")

    for campo in payload:
        if campo not in CONTRATO:
            erros.append(f"campo fora do contrato: {campo}")

    if erros:
        return erros

    for campo, permitidos in VALORES_PERMITIDOS.items():
        if payload[campo] not in permitidos:
            erros.append(f"valor não permitido em {campo}: {payload[campo]!r}")

    for campo, (minimo, maximo) in FAIXAS.items():
        if not minimo <= payload[campo] <= maximo:
            erros.append(f"{campo} fora da faixa [{minimo}, {maximo}]: {payload[campo]}")

    if not (payload["cnes"].isdigit() and len(payload["cnes"]) == 7):
        erros.append("cnes deve ter 7 dígitos")
    if not (payload["cod_municipio"].isdigit() and len(payload["cod_municipio"]) == 6):
        erros.append("cod_municipio deve ter 6 dígitos")

    return erros


def preparar_csv():
    if CSV_FILE.exists():
        with CSV_FILE.open(encoding="utf-8") as arquivo:
            cabecalho = arquivo.readline().strip()
        if cabecalho == ",".join(CSV_FIELDS):
            return
        backup = CSV_FILE.with_name(f"dados_formato_antigo_{datetime.now():%Y%m%d_%H%M%S}.csv")
        CSV_FILE.rename(backup)
        print(f"CSV com formato antigo movido para {backup.name}")
    with CSV_FILE.open("w", newline="", encoding="utf-8") as arquivo:
        csv.writer(arquivo).writerow(CSV_FIELDS)


def gravar_leitura(payload):
    linha = {"data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **payload}
    linha_csv = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in linha.items()}
    with CSV_FILE.open("a", newline="", encoding="utf-8") as arquivo:
        csv.DictWriter(arquivo, fieldnames=CSV_FIELDS).writerow(linha_csv)
    return linha


def registrar_rejeicao(origem, motivo, conteudo):
    global total_rejeitadas
    total_rejeitadas += 1
    trecho = conteudo[:200].replace("\n", "\\n")
    with LOG_REJEITADOS.open("a", encoding="utf-8") as log:
        log.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | origem={origem} | {motivo} | {trecho}\n")
    print(f"[REJEITADA] {origem}: {motivo}")


def receber_mensagem(conn):
    dados = b""
    while b"\n" not in dados:
        pedaco = conn.recv(1024)
        if not pedaco:
            break
        dados += pedaco
        if len(dados) > TAMANHO_MAXIMO_BYTES:
            raise ValueError(f"mensagem maior que {TAMANHO_MAXIMO_BYTES} bytes")
    return dados


def exibir(linha):
    print("JSON recebido e gravado:")
    print(json.dumps(linha, indent=2, ensure_ascii=False))
    resumo = " · ".join(f"{s} {contagem_status[s]}" for s in ("OK", "ALERTA", "LOTADO", "SEM_LEITURA"))
    print(f"Indicador | gravadas: {sum(contagem_status.values())} ({resumo}) | rejeitadas: {total_rejeitadas}")
    print("-" * 70)


def tratar_mensagem(dados, origem):
    try:
        texto = dados.decode("utf-8").strip()
    except UnicodeDecodeError:
        registrar_rejeicao(origem, "bytes não são texto UTF-8", repr(dados))
        return

    if not texto:
        return

    try:
        payload = json.loads(texto)
    except json.JSONDecodeError as erro:
        registrar_rejeicao(origem, f"JSON inválido ({erro.msg})", texto)
        return

    erros = validar(payload)
    if erros:
        registrar_rejeicao(origem, "; ".join(erros), texto)
        return

    linha = gravar_leitura(payload)
    contagem_status[payload["status"]] += 1
    exibir(linha)


def iniciar_servidor():
    preparar_csv()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORT))
        servidor.listen()
        print(f"Servidor Pulso aguardando na porta {PORT}...")
        print("-" * 70)
        while True:
            conn, endereco = servidor.accept()
            origem = f"{endereco[0]}:{endereco[1]}"
            with conn:
                try:
                    conn.settimeout(TIMEOUT_CONEXAO_S)
                    tratar_mensagem(receber_mensagem(conn), origem)
                except socket.timeout:
                    registrar_rejeicao(origem, "conexão sem dados (timeout)", "")
                except ValueError as erro:
                    registrar_rejeicao(origem, str(erro), "")
                except Exception as erro:
                    registrar_rejeicao(origem, f"erro inesperado: {type(erro).__name__}: {erro}", "")


if __name__ == "__main__":
    try:
        iniciar_servidor()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        print(f"Resumo: {dict(contagem_status)} | rejeitadas: {total_rejeitadas}")
