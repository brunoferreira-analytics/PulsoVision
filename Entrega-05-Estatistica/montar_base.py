# PulsoVision · Retrato do Acesso à Saúde
# Disciplina 05: Statistical Computing with R & Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 05-estatistica/montar_base.py
# Resumo:  Monta a base da análise (base_municipios.csv): uma linha por município
#          brasileiro, com a população estimada do IBGE (2026) e a contagem dos
#          estabelecimentos de saúde ativos no CNES/DataSUS (set/2026). Procura os
#          arquivos brutos sozinho, na mesma pasta ou em dados_brutos/. Lê só as
#          colunas sem dados pessoais do CNES (nada de CPF, e-mail ou telefone),
#          conforme a LGPD. Também é chamado pelo analise_estatistica.py.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
PASTAS_BUSCA = [PASTA, PASTA / "dados_brutos"]
PADRAO_CNES = "tbEstabelecimento*.csv"
PADRAO_IBGE = "estimativa_dou*.xls*"
DESTINO = PASTA / "base_municipios.csv"

# Só colunas sem dado pessoal: o CPF, o e-mail e o telefone nunca são lidos.
COLUNAS_CNES = [
    "CO_CNES",
    "TP_UNIDADE",
    "CO_MUNICIPIO_GESTOR",
    "CO_MOTIVO_DESAB",
    "TP_ESTAB_SEMPRE_ABERTO",
    "ST_CONEXAO_INTERNET",
    "CO_NATUREZA_JUR",
]

# Tipos de unidade do CNES (TP_UNIDADE)
TIPOS_UBS = {"01", "02"}               # posto de saúde e centro de saúde/UBS
TIPOS_HOSPITAL = {"05", "07", "15"}    # hospital geral, especializado e unidade mista
TIPOS_PRONTO = {"20", "21", "73"}      # pronto-socorro geral, especializado e pronto atendimento (UPA)

REGIOES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}


def localizar(padrao: str) -> Path | None:
    """Devolve o arquivo mais recente que casa com o padrão, ou None."""
    achados = [arquivo for pasta in PASTAS_BUSCA if pasta.is_dir() for arquivo in pasta.glob(padrao)]
    return max(achados, key=lambda arquivo: arquivo.stat().st_mtime) if achados else None


def ler_cnes(caminho: Path) -> pd.DataFrame:
    cnes = pd.read_csv(caminho, sep=";", encoding="latin-1", usecols=COLUNAS_CNES, dtype=str)
    ativos = cnes[cnes["CO_MOTIVO_DESAB"].isna()].copy()

    ativos["ubs"] = ativos["TP_UNIDADE"].isin(TIPOS_UBS)
    ativos["hospitais"] = ativos["TP_UNIDADE"].isin(TIPOS_HOSPITAL)
    ativos["pronto_atendimento"] = ativos["TP_UNIDADE"].isin(TIPOS_PRONTO)
    ativos["estab_publicos"] = ativos["CO_NATUREZA_JUR"].str.startswith("1")
    ativos["estab_24h"] = ativos["TP_ESTAB_SEMPRE_ABERTO"].eq("S")
    ativos["estab_com_internet"] = ativos["ST_CONEXAO_INTERNET"].eq("S")

    return ativos.groupby("CO_MUNICIPIO_GESTOR").agg(
        estab_ativos=("CO_CNES", "count"),
        estab_publicos=("estab_publicos", "sum"),
        ubs=("ubs", "sum"),
        hospitais=("hospitais", "sum"),
        pronto_atendimento=("pronto_atendimento", "sum"),
        estab_24h=("estab_24h", "sum"),
        estab_com_internet=("estab_com_internet", "sum"),
    )


def ler_ibge(caminho: Path) -> pd.DataFrame:
    planilhas = pd.ExcelFile(caminho).sheet_names
    aba = next(nome for nome in planilhas if nome.lower().startswith("munic"))
    bruto = pd.read_excel(caminho, sheet_name=aba, header=None, dtype=str)

    # O cabeçalho do IBGE não fica na primeira linha: procura a linha com "COD. MUNIC".
    linha = bruto.index[bruto.apply(lambda r: r.str.strip().eq("COD. MUNIC").any(), axis=1)][0]
    ibge = bruto.iloc[linha + 1:].set_axis(bruto.iloc[linha].str.strip(), axis=1)
    ibge = ibge.dropna(subset=["COD. MUNIC"])
    ibge = ibge[ibge["COD. MUNIC"].str.strip().str.isdigit()]

    ibge["cod_ibge"] = ibge["COD. UF"].str.strip().str.zfill(2) + ibge["COD. MUNIC"].str.strip().str.zfill(5)
    ibge["populacao"] = pd.to_numeric(
        ibge["POPULAÇÃO ESTIMADA"].str.replace(r"\D", "", regex=True), errors="coerce"
    )
    return pd.DataFrame({
        "cod_ibge": ibge["cod_ibge"],
        "cod_ibge6": ibge["cod_ibge"].str[:6],
        "municipio": ibge["NOME DO MUNICÍPIO"].str.strip(),
        "uf": ibge["UF"].str.strip(),
        "regiao": ibge["cod_ibge"].str[0].map(REGIOES),
        "populacao": ibge["populacao"].astype(int),
    })


def montar(cnes: pd.DataFrame, ibge: pd.DataFrame) -> pd.DataFrame:
    base = ibge.merge(cnes, left_on="cod_ibge6", right_index=True, how="left")
    contagens = ["estab_ativos", "estab_publicos", "ubs", "hospitais",
                 "pronto_atendimento", "estab_24h", "estab_com_internet"]
    base[contagens] = base[contagens].fillna(0).astype(int)

    por_10mil = 10_000 / base["populacao"]
    base["ubs_10mil"] = (base["ubs"] * por_10mil).round(4)
    base["estab_10mil"] = (base["estab_ativos"] * por_10mil).round(4)
    base["estab_publicos_10mil"] = (base["estab_publicos"] * por_10mil).round(4)
    base["pct_internet"] = (100 * base["estab_com_internet"] / base["estab_ativos"]).round(2)
    base["pct_publicos"] = (100 * base["estab_publicos"] / base["estab_ativos"]).round(2)
    base["log10_populacao"] = np.log10(base["populacao"]).round(4)
    base["tem_hospital_ou_pa"] = ((base["hospitais"] + base["pronto_atendimento"]) > 0).astype(int)
    return base.sort_values("cod_ibge").reset_index(drop=True)


def gerar_base(cnes_path: Path, ibge_path: Path) -> Path:
    print(f"Lendo o CNES ({cnes_path.name}) e o IBGE ({ibge_path.name})...")
    base = montar(ler_cnes(cnes_path), ler_ibge(ibge_path))
    base.to_csv(DESTINO, index=False, encoding="utf-8")
    print(f"Base gravada em {DESTINO.name}: {len(base)} municípios, "
          f"{base['estab_ativos'].sum()} estabelecimentos ativos.")
    return DESTINO


def garantir_base() -> Path:
    """Monta a base quando os arquivos brutos estão na pasta e a base falta ou está
    mais velha que eles. Sem os brutos, usa a base_municipios.csv que já existe."""
    cnes_path, ibge_path = localizar(PADRAO_CNES), localizar(PADRAO_IBGE)
    tem_brutos = cnes_path is not None and ibge_path is not None

    if tem_brutos:
        desatualizada = not DESTINO.exists() or DESTINO.stat().st_mtime < max(
            cnes_path.stat().st_mtime, ibge_path.stat().st_mtime)
        if desatualizada:
            return gerar_base(cnes_path, ibge_path)
        print(f"Usando {DESTINO.name} (já está em dia com o CNES e o IBGE da pasta).")
        return DESTINO

    if DESTINO.exists():
        print(f"Arquivos brutos não encontrados: usando {DESTINO.name}.")
        return DESTINO

    sys.exit("Não achei a base_municipios.csv nem os arquivos brutos "
             f"({PADRAO_CNES} e {PADRAO_IBGE}) nesta pasta ou em dados_brutos/.")


def main() -> None:
    cnes_path = Path(sys.argv[1]) if len(sys.argv) > 1 else localizar(PADRAO_CNES)
    ibge_path = Path(sys.argv[2]) if len(sys.argv) > 2 else localizar(PADRAO_IBGE)
    if cnes_path is None or ibge_path is None:
        sys.exit(f"Coloque o {PADRAO_CNES} e o {PADRAO_IBGE} nesta pasta ou em dados_brutos/.")
    gerar_base(cnes_path, ibge_path)


if __name__ == "__main__":
    main()
