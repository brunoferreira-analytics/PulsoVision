# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/gerar_matriz_riscos.py
# Resumo:  Desenha a matriz probabilidade × impacto antes e depois das medidas a
#          partir de riscos.json.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PASTA = Path(__file__).resolve().parent


def nivel(pontos):
    return "Crítico" if pontos >= 15 else "Alto" if pontos >= 10 else "Médio" if pontos >= 5 else "Baixo"


def desenhar(eixo, riscos, chave_p, chave_i, titulo):
    cores = np.zeros((5, 5, 3))
    for p in range(1, 6):
        for i in range(1, 6):
            cores[p - 1, i - 1] = {"Crítico": (0.80, 0.25, 0.22), "Alto": (0.93, 0.55, 0.30),
                                   "Médio": (0.97, 0.85, 0.45), "Baixo": (0.62, 0.80, 0.55)}[nivel(p * i)]
    eixo.imshow(cores, origin="lower", extent=(0.5, 5.5, 0.5, 5.5))
    celulas = {}
    for r in riscos:
        celulas.setdefault((r[chave_i], r[chave_p]), []).append(r["id"])
    for (i, p), ids in celulas.items():
        eixo.text(i, p, "\n".join(", ".join(ids[k:k + 2]) for k in range(0, len(ids), 2)), ha="center",
                  va="center", fontsize=8.5, fontweight="bold")
    eixo.set_xticks(range(1, 6), ["1\nmínimo", "2", "3", "4", "5\ngrave"])
    eixo.set_yticks(range(1, 6), ["1 rara", "2", "3", "4", "5 quase certa"])
    eixo.set_xlabel("Impacto")
    eixo.set_ylabel("Probabilidade")
    eixo.set_title(titulo)


def main():
    riscos = json.loads((PASTA / "riscos.json").read_text(encoding="utf-8"))
    fig, eixos = plt.subplots(1, 2, figsize=(14, 6.2))
    desenhar(eixos[0], riscos, "p", "i", "Antes das medidas")
    desenhar(eixos[1], riscos, "p2", "i2", "Depois das medidas (risco residual)")
    plt.suptitle("PulsoVision · matriz de riscos (probabilidade × impacto)", fontsize=14)
    plt.tight_layout()
    saida = PASTA / "evidencias" / "matriz_riscos_antes_depois.png"
    plt.savefig(saida, dpi=150)
    for r in sorted(riscos, key=lambda r: -r["p"] * r["i"]):
        print(f"{r['id']} {r['p'] * r['i']:>2} {nivel(r['p'] * r['i']):<8} -> {r['p2'] * r['i2']:>2} "
              f"{nivel(r['p2'] * r['i2']):<8} {r['risco']}")
    print(f"Figura: {saida}")


if __name__ == "__main__":
    main()
