# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/gerar_segredos.py
# Resumo:  Gera os segredos dos totens e os tokens dos perfis gestor e auditor.
#          Grava o cofre fora do Git (permissão 600) e mostra os valores uma única vez.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import sys

from seguranca.credenciais import CAMINHO_PADRAO, gerar


def main():
    if CAMINHO_PADRAO.exists() and "--sobrescrever" not in sys.argv:
        print(f"Já existe {CAMINHO_PADRAO}. Use --sobrescrever para gerar novos segredos (os antigos deixam de valer).")
        return
    entregar = gerar(CAMINHO_PADRAO)
    print(f"Segredos gravados em {CAMINHO_PADRAO} (fora do Git, permissão 600).")
    print("\nCopie AGORA; eles não serão mostrados de novo:\n")
    for id_totem, segredo in entregar["totens"].items():
        print(f"  segredo do {id_totem}: {segredo}")
    for perfil, token in entregar["tokens"].items():
        print(f"  token do perfil {perfil}: {token}")


if __name__ == "__main__":
    main()
