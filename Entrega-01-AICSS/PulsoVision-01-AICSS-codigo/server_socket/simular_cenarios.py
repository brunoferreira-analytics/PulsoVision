# PulsoVision · Totem de Lotação
# Disciplina 01: AI Computer Systems & Sensors (AICSS) · Global Solution 2026.2 — FIAP
#
# Arquivo: 01-aicss-totem/server_socket/simular_cenarios.py
# Resumo:  Cliente de teste do servidor. Envia quatro leituras válidas e,
#          com --invalidos, seis mensagens inválidas para comprovar a
#          validação. As leituras saem com id_totem SIMULADOR-01 (não é o
#          ESP32).
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import json
import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 5000

BASE = {
    "versao_contrato": "1.0",
    "id_totem": "SIMULADOR-01",
    "cnes": "4048296",
    "nome_unidade": "UBS Jardim Paulista",
    "tipo_unidade": "UBS",
    "cod_municipio": "351880",
}

CENARIOS_VALIDOS = [
    ("1. Fila curta (OK)", {"fila_distancia_cm": 400.0, "fila_status": "CURTA", "movimento": True,
                            "movimento_status": "FLUXO", "pessoas_aguardando": 0, "status": "OK",
                            "motivo": "FILA_CURTA"}),
    ("2. Fila média andando (ALERTA)", {"fila_distancia_cm": 200.0, "fila_status": "MEDIA", "movimento": True,
                                       "movimento_status": "FLUXO", "pessoas_aguardando": 3,
                                       "status": "ALERTA", "motivo": "FILA_MEDIA"}),
    ("3. Fila média parada (LOTADO)", {"fila_distancia_cm": 200.0, "fila_status": "MEDIA", "movimento": False,
                                      "movimento_status": "SEM_FLUXO", "pessoas_aguardando": 3,
                                      "status": "LOTADO", "motivo": "FILA_PARADA"}),
    ("4. Fila longa (LOTADO)", {"fila_distancia_cm": 80.0, "fila_status": "LONGA", "movimento": True,
                               "movimento_status": "FLUXO", "pessoas_aguardando": 5,
                               "status": "LOTADO", "motivo": "FILA_LONGA"}),
]

MENSAGENS_INVALIDAS = [
    ("A. JSON quebrado", b"{\"status\": \"OK\"\n"),
    ("B. JSON que nao e objeto", b"[1, 2, 3]\n"),
    ("C. Campos faltando", json.dumps({"cnes": "4048296", "status": "OK"}).encode() + b"\n"),
    ("D. Status fora do contrato", json.dumps({**BASE, **CENARIOS_VALIDOS[0][1], "id_leitura": 99,
                                               "status": "TUDO_CERTO"}).encode() + b"\n"),
    ("E. Campo injetado", json.dumps({**BASE, **CENARIOS_VALIDOS[0][1], "id_leitura": 98,
                                      "comando": "apagar_tudo"}).encode() + b"\n"),
    ("F. Mensagem gigante (> 4 KB)", b"{\"x\": \"" + b"A" * 6000 + b"\"}\n"),
]


def enviar(conteudo):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        cliente.connect((HOST, PORT))
        cliente.sendall(conteudo)
    time.sleep(0.3)


def main():
    print("SIMULAÇÃO (não é o ESP32) — id_totem = SIMULADOR-01\n")
    for numero, (nome, campos) in enumerate(CENARIOS_VALIDOS, start=1):
        enviar((json.dumps({**BASE, "id_leitura": numero, **campos}) + "\n").encode("utf-8"))
        print(f"enviado: {nome}")

    if "--invalidos" in sys.argv:
        print("\nMensagens inválidas (o servidor deve recusar e continuar no ar):")
        for nome, conteudo in MENSAGENS_INVALIDAS:
            try:
                enviar(conteudo)
                print(f"enviado: {nome}")
            except OSError as erro:
                print(f"falhou ao enviar {nome}: {erro}")

        enviar((json.dumps({**BASE, "id_leitura": 100, **CENARIOS_VALIDOS[0][1]}) + "\n").encode("utf-8"))
        print("\nenviado: leitura válida final (prova de que o servidor seguiu no ar)")


if __name__ == "__main__":
    try:
        main()
    except ConnectionRefusedError:
        print("Servidor não está rodando.")
