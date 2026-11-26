# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/executar.py
# Resumo:  Sobe a API segura só na máquina local. Com --https gera um certificado de
#          demonstração e liga TLS (em produção o certificado vem de uma CA).
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import argparse
import datetime
import ipaddress
from pathlib import Path

from app_segura import create_app_segura

PASTA_CERTS = Path(__file__).resolve().parent / "certs"


def gerar_certificado(pasta=PASTA_CERTS):
    """Certificado autoassinado só para demonstração local. Em produção: certificado de uma CA (ex.: Let's Encrypt)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    certificado, chave = pasta / "pulso.crt", pasta / "pulso.key"
    if certificado.exists() and chave.exists():
        return certificado, chave
    pasta.mkdir(exist_ok=True)
    privada = ec.generate_private_key(ec.SECP256R1())
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PulsoVision (demo)")])
    agora = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(nome).issuer_name(nome).public_key(privada.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(agora)
            .not_valid_after(agora + datetime.timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost"),
                                                        x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
                           critical=False)
            .sign(privada, hashes.SHA256()))
    certificado.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    chave.write_bytes(privada.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                            serialization.NoEncryption()))
    chave.chmod(0o600)
    return certificado, chave


def main():
    parser = argparse.ArgumentParser(description="Sobe a API segura do PulsoVision.")
    parser.add_argument("--https", action="store_true", help="liga TLS com certificado de demonstração")
    parser.add_argument("--porta", type=int, default=5443)
    args = parser.parse_args()
    app = create_app_segura()
    contexto = tuple(map(str, gerar_certificado())) if args.https else None
    # Escuta só na máquina local; a exposição externa passa pelo proxy reverso (ver documentação).
    app.run(host="127.0.0.1", port=args.porta, ssl_context=contexto, debug=False)


if __name__ == "__main__":
    main()
