# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/ia/gerar_manifesto_modelos.py
# Resumo:  Publica o SHA-256 dos modelos treinados (06 e 07) num manifesto, usado
#          para recusar arquivo de modelo trocado.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import argparse
from pathlib import Path

from guardrails import gerar_manifesto

PASTA = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Publica o SHA-256 dos modelos treinados (06 e 07).")
    parser.add_argument("modelos", nargs="+", help="ex.: ../../06-machine-learning/modelo_vazio_urgencia.joblib")
    parser.add_argument("--saida", default=str(PASTA / "manifesto_modelos.json"))
    args = parser.parse_args()
    for nome, resumo in gerar_manifesto([m for m in args.modelos if Path(m).exists()], args.saida).items():
        print(f"{nome}: {resumo}")
    print(f"Manifesto gravado em {args.saida}")


if __name__ == "__main__":
    main()
