# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/totem_simulado.py
# Resumo:  Totem simulado: envia uma leitura do jeito que o firmware deve enviar,
#          com corpo JSON, horário, nonce e assinatura HMAC-SHA256, por HTTPS.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import argparse
import json
import secrets
import ssl
import time
import urllib.error
import urllib.request

from seguranca.assinatura import assinar


def enviar(url, id_totem, segredo, leitura, ca=None):
    """Envia uma leitura do jeito que o firmware do totem deve fazer: corpo JSON + assinatura HMAC."""
    corpo = json.dumps(leitura, ensure_ascii=False).encode("utf-8")
    timestamp, nonce = str(int(time.time())), secrets.token_hex(12)
    pedido = urllib.request.Request(url, data=corpo, method="POST", headers={
        "Content-Type": "application/json", "X-Totem-Id": id_totem, "X-Timestamp": timestamp,
        "X-Nonce": nonce, "X-Assinatura": assinar(segredo, timestamp, nonce, corpo)})
    contexto = ssl.create_default_context(cafile=ca) if ca else None
    try:
        with urllib.request.urlopen(pedido, timeout=5, context=contexto) as resposta:
            return resposta.status, json.loads(resposta.read())
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read())


def main():
    parser = argparse.ArgumentParser(description="Totem simulado com leitura assinada.")
    parser.add_argument("--url", default="https://127.0.0.1:5443/leituras")
    parser.add_argument("--totem", default="TOTEM-4048296-01")
    parser.add_argument("--segredo", required=True, help="segredo do totem, mostrado por gerar_segredos.py")
    parser.add_argument("--ca", default="certs/pulso.crt", help="certificado em que o totem confia")
    args = parser.parse_args()
    leitura = {"versao_contrato": "1.0", "id_leitura": int(time.time()) % 10_000_000, "id_totem": args.totem,
               "cnes": args.totem.split("-")[1], "nome_unidade": "UBS", "tipo_unidade": "UBS",
               "cod_municipio": "351880", "fila_distancia_cm": 42.5, "fila_status": "LONGA", "movimento": True,
               "movimento_status": "FLUXO", "pessoas_aguardando": 6, "status": "LOTADO", "motivo": "FILA_LONGA"}
    status, resposta = enviar(args.url, args.totem, args.segredo, leitura, args.ca if args.url.startswith("https") else None)
    print(status, json.dumps(resposta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
