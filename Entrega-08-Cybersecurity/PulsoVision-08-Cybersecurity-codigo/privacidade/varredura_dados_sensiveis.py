# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/privacidade/varredura_dados_sensiveis.py
# Resumo:  Varredura LGPD: procura CPF (com dígito verificador), e-mail, telefone,
#          chaves da AWS e chaves privadas em arquivos e pastas. Nunca imprime os
#          valores. Com --falhar serve de verificação antes do commit.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PADROES = {
    "cpf": re.compile(r"(?<![\d.])(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?![\d.])"),
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "telefone": re.compile(r"\(\d{2}\)\s?9?\d{4}-?\d{4}|(?<!\d)\d{2}\s9\d{4}-\d{4}(?!\d)"),
    "chave_aws": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "segredo_aws": re.compile(r"aws_(?:secret_access_key|session_token)\s*[=:]\s*\S{16,}", re.I),
    "chave_privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
COLUNAS_SENSIVEIS = re.compile(r"CPF|EMAIL|TELEFONE|FAX|USUARIO|DIRETOR|CELULAR|NOME_PACIENTE", re.I)
MARCA_IGNORAR = "varredura: ignorar"
EXTENSOES = {".csv", ".txt", ".py", ".ipynb", ".json", ".md", ".ino", ".hpp", ".h", ".toml", ".env", ".cfg", ".ini",
             ".yaml", ".yml", ".log", ".jsonl"}


def cpf_valido(texto):
    """Só conta como CPF se os dois dígitos verificadores baterem (reduz falso positivo)."""
    d = [int(c) for c in texto if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        resto = sum(d[i] * (n + 1 - i) for i in range(n)) * 10 % 11
        if resto % 10 != d[n]:
            return False
    return True


def contar_linha(linha, contagem):
    for nome, padrao in PADROES.items():
        achados = padrao.findall(linha)
        if nome == "cpf":
            achados = [a for a in achados if cpf_valido(a)]
        contagem[nome] += len(achados)


def colunas_sensiveis_csv(caminho):
    """Para CSV com cabeçalho: quantos valores preenchidos existem em colunas que guardam dado pessoal."""
    with caminho.open(encoding="latin-1", newline="") as arquivo:
        amostra = arquivo.readline()
        separador = ";" if amostra.count(";") > amostra.count(",") else ","
        arquivo.seek(0)
        leitor = csv.reader(arquivo, delimiter=separador)
        cabecalho = next(leitor, [])
        alvos = [i for i, c in enumerate(cabecalho) if COLUNAS_SENSIVEIS.search(c)]
        preenchidos = {cabecalho[i]: 0 for i in alvos}
        linhas = 0
        for linha in leitor:
            linhas += 1
            for i in alvos:
                if i < len(linha) and linha[i].strip():
                    preenchidos[cabecalho[i]] += 1
    return linhas, preenchidos


def varrer_arquivo(caminho):
    contagem = dict.fromkeys(PADROES, 0)
    with caminho.open(encoding="latin-1", errors="ignore") as arquivo:
        for linha in arquivo:
            if MARCA_IGNORAR not in linha:  # dado fictício de teste, marcado no próprio código
                contar_linha(linha, contagem)
    resultado = {"arquivo": str(caminho), "achados": contagem, "total": sum(contagem.values())}
    if caminho.suffix.lower() == ".csv":
        resultado["linhas"], resultado["colunas_sensiveis"] = colunas_sensiveis_csv(caminho)
    return resultado


def listar(alvos):
    for alvo in map(Path, alvos):
        if alvo.is_file():
            yield alvo
        elif alvo.is_dir():
            for p in sorted(alvo.rglob("*")):
                if p.is_file() and p.suffix.lower() in EXTENSOES and not any(
                        parte in {".git", ".venv", "__pycache__", "node_modules"} for parte in p.parts):
                    yield p


def main():
    parser = argparse.ArgumentParser(description="Procura dado pessoal e credencial em arquivos. Nunca imprime os valores.")
    parser.add_argument("alvos", nargs="+", help="arquivos ou pastas")
    parser.add_argument("--json", help="grava o resultado neste arquivo")
    parser.add_argument("--falhar", action="store_true", help="sai com código 1 se achar algo (uso em pre-commit)")
    args = parser.parse_args()
    resultados = [varrer_arquivo(p) for p in listar(args.alvos)]
    for r in resultados:
        if r["total"] or r.get("colunas_sensiveis"):
            partes = [f"{k}: {v}" for k, v in r["achados"].items() if v]
            colunas = {k: v for k, v in (r.get("colunas_sensiveis") or {}).items() if v}
            print(f"[ACHOU] {r['arquivo']} | {', '.join(partes) or 'nenhum padrão'}"
                  + (f" | colunas pessoais preenchidas: {colunas}" if colunas else ""))
    limpos = sum(1 for r in resultados if not r["total"] and not any((r.get("colunas_sensiveis") or {}).values()))
    print(f"{len(resultados)} arquivo(s) varrido(s), {limpos} sem dado pessoal ou credencial.")
    if args.json:
        Path(args.json).write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.falhar and limpos < len(resultados):
        sys.exit(1)


if __name__ == "__main__":
    main()
