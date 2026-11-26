# PulsoVision · Retrato do Acesso à Saúde
# Disciplina 05: Statistical Computing with R & Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 05-estatistica/analise_estatistica.py
# Resumo:  Responde às questões 02 a 06 da Global Solution com dados reais dos
#          5.571 municípios brasileiros (CNES/DataSUS set/2026 + IBGE 2026):
#          distribuição Normal, teste de hipótese para a média, regressão linear
#          simples e múltipla e regressão logística binária. Antes, monta a base
#          sozinho se o CNES e o IBGE brutos estiverem na pasta (montar_base.py).
#          Os gráficos vão para a pasta graficos/ e os números aparecem no terminal.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

from math import log10, sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import norm
from sklearn.metrics import accuracy_score, confusion_matrix

from montar_base import garantir_base

PASTA = Path(__file__).resolve().parent
GRAFICOS = PASTA / "graficos"
SEMENTE = 2026  # semente fixa: as amostras da questão 03 saem sempre iguais

NOMES = {
    "ubs_10mil": "UBS por 10 mil habitantes",
    "log10_populacao": "População (log10 de habitantes)",
    "pct_publicos": "Estabelecimentos públicos (%)",
    "pct_internet": "Estabelecimentos com internet (%)",
    "estab_10mil": "Estabelecimentos por 10 mil habitantes",
    "tem_hospital_ou_pa": "Tem hospital ou pronto atendimento",
}

CURTOS = {  # rótulos curtos para matrizes e grades de gráficos
    "ubs_10mil": "UBS/10 mil hab.",
    "log10_populacao": "log10(população)",
    "pct_publicos": "% públicos",
    "pct_internet": "% com internet",
}

sns.set_theme(style="whitegrid", context="notebook")


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def salvar(nome: str) -> None:
    plt.tight_layout()
    plt.savefig(GRAFICOS / nome, dpi=150)
    plt.close()


def classificar(p: float) -> str:
    if np.isclose(p, 0.5):
        return "evento igualmente provável (equiprovável)"
    return "evento muito provável" if p > 0.5 else "evento pouco provável"


# ---------------------------------------------------------------------------
# 01) Base de dados
# ---------------------------------------------------------------------------
def questao_01(dados: pd.DataFrame) -> None:
    titulo("01) Base de dados: CNES/DataSUS (set/2026) + IBGE (estimativa 2026)")
    print(f"Municípios: {len(dados)}")
    print(f"População total: {dados['populacao'].sum():,}".replace(",", "."))
    print(f"Estabelecimentos de saúde ativos: {dados['estab_ativos'].sum():,}".replace(",", "."))
    print(f"UBS e postos de saúde ativos: {dados['ubs'].sum():,}".replace(",", "."))
    colunas = ["ubs_10mil", "estab_10mil", "pct_publicos", "pct_internet", "log10_populacao"]
    print("\nResumo das variáveis quantitativas:")
    print(dados[colunas].describe().round(3).to_string())

    faixas = pd.cut(dados["populacao"], [0, 5_000, 20_000, 100_000, 500_000, np.inf],
                    labels=["até 5 mil", "5 a 20 mil", "20 a 100 mil", "100 a 500 mil", "mais de 500 mil"])
    resumo = dados.groupby(faixas, observed=True).agg(
        municipios=("ubs_10mil", "size"),
        ubs_10mil=("ubs_10mil", "mean"),
        com_hospital_ou_pa=("tem_hospital_ou_pa", "mean"),
    )
    resumo["com_hospital_ou_pa"] *= 100
    print("\nPor porte do município:")
    print(resumo.round(2).to_string())


# ---------------------------------------------------------------------------
# 02) Distribuição Normal
# ---------------------------------------------------------------------------
def questao_02(dados: pd.DataFrame) -> None:
    titulo("02) Distribuição Normal: UBS por 10 mil habitantes")
    x = dados["ubs_10mil"]
    media, mediana = x.mean(), x.median()
    dp = x.std(ddof=0)  # a base cobre todos os municípios: desvio padrão populacional
    print(f"Média = {media:.4f} | Mediana = {mediana:.4f} | Desvio padrão = {dp:.4f}")

    p_a = norm.cdf(media, media, dp)
    print(f"a) P(X < {media:.4f}) = {p_a:.4f} -> {classificar(p_a)}")
    p_b = norm.sf(mediana, media, dp)
    print(f"b) P(X > {mediana:.4f}) = {p_b:.4f} -> {classificar(p_b)}")

    eixo = np.linspace(0, 20, 400)
    plt.figure(figsize=(9, 5))
    sns.histplot(x[x <= 20], bins=60, stat="density", color="#9bbcd9", label="Municípios")
    plt.plot(eixo, norm.pdf(eixo, media, dp), color="#1f4e79", lw=2, label="Curva Normal ajustada")
    plt.axvline(media, color="#c0392b", ls="--", lw=1.5, label=f"Média = {media:.2f}")
    plt.axvline(mediana, color="#27864a", ls=":", lw=2, label=f"Mediana = {mediana:.2f}")
    plt.title("Distribuição das UBS por 10 mil habitantes nos municípios")
    plt.xlabel(NOMES["ubs_10mil"])
    plt.ylabel("Densidade")
    plt.legend()
    salvar("q02_normal_ubs.png")


# ---------------------------------------------------------------------------
# 03) Teste de hipótese para a média
# ---------------------------------------------------------------------------
def teste_z(amostra: pd.Series, mu: float, sigma: float, alfa: float, cauda: str) -> float:
    n, x_barra = len(amostra), amostra.mean()
    zc = (x_barra - mu) / (sigma / sqrt(n))
    za = norm.ppf(alfa) if cauda == "esquerda" else norm.ppf(1 - alfa)
    rejeita = zc < za if cauda == "esquerda" else zc > za
    print(f"   n = {n} | média amostral = {x_barra:.4f}")
    print(f"   Zc = {zc:.4f} | Za = {za:.4f}")
    print(f"   Decisão: {'Rejeita H0' if rejeita else 'Aceita H0'}")
    return zc


def questao_03(dados: pd.DataFrame) -> None:
    titulo("03) Teste de hipótese para a média: UBS por 10 mil habitantes")
    mu = dados["ubs_10mil"].mean()
    sigma = dados["ubs_10mil"].std(ddof=0)
    print(f"Média populacional de referência (Brasil) = {mu:.4f} | desvio padrão populacional = {sigma:.4f}")

    grandes = dados[dados["populacao"] > 100_000]
    amostra_a = grandes["ubs_10mil"].sample(n=20, random_state=SEMENTE)
    print(f"\na) Amostra aleatória de 20 dos {len(grandes)} municípios com mais de 100 mil habitantes")
    print(f"   H0: mu >= {mu:.4f} | H1: mu < {mu:.4f} | alfa = 6%")
    teste_z(amostra_a, mu, sigma, 0.06, "esquerda")

    pequenos = dados[dados["populacao"] <= 5_000]
    amostra_b = pequenos["ubs_10mil"].sample(n=25, random_state=SEMENTE)
    print(f"\nb) Amostra aleatória de 25 dos {len(pequenos)} municípios com até 5 mil habitantes")
    print(f"   H0: mu <= {mu:.4f} | H1: mu > {mu:.4f} | alfa = 9%")
    teste_z(amostra_b, mu, sigma, 0.09, "direita")


# ---------------------------------------------------------------------------
# 04) Análise bivariada
# ---------------------------------------------------------------------------
def questao_04(dados: pd.DataFrame) -> None:
    titulo("04) Análise bivariada: população (log10) x UBS por 10 mil habitantes")
    x, y = "log10_populacao", "ubs_10mil"

    plt.figure(figsize=(9, 5.5))
    sns.scatterplot(x=x, y=y, data=dados, s=12, alpha=0.35, edgecolor=None)
    plt.title("Dispersão: tamanho do município x UBS por 10 mil habitantes")
    plt.xlabel(NOMES[x])
    plt.ylabel(NOMES[y])
    salvar("q04a_dispersao.png")

    covariancia = np.cov(dados[x], dados[y])[0, 1]
    correlacao = np.corrcoef(dados[x], dados[y])[0, 1]
    print(f"b) Covariância = {covariancia:.4f} | Correlação de Pearson r = {correlacao:.4f}")

    plt.figure(figsize=(7, 5))
    sns.heatmap(dados[[x, y]].rename(columns=CURTOS).corr(), annot=True, fmt=".3f",
                cmap="coolwarm", vmin=-1, vmax=1, square=True)
    plt.yticks(rotation=0)
    plt.title("Mapa de Correlação Linear de Pearson")
    salvar("q04c_correlacao.png")

    modelo = sm.OLS(dados[y], sm.add_constant(dados[x])).fit()
    b0, b1 = modelo.params
    plt.figure(figsize=(9, 5.5))
    sns.regplot(x=x, y=y, data=dados, ci=None, scatter_kws={"s": 12, "alpha": 0.35},
                line_kws={"color": "red"})
    plt.title("Gráfico de Dispersão com Reta de Regressão")
    plt.xlabel(NOMES[x])
    plt.ylabel(NOMES[y])
    salvar("q04d_regressao.png")
    print(f"d) Equação: UBS por 10 mil = {b0:.4f} + ({b1:.4f}) x log10(população)")

    print(f"e) R² = {modelo.rsquared:.4f} | F = {modelo.fvalue:.2f} | p-valor do F = {modelo.f_pvalue:.3e}")
    print(modelo.summary())

    for habitantes in (10_000, 50_000):
        previsto = b0 + b1 * log10(habitantes)
        print(f"f) Município com {habitantes:,} habitantes -> {previsto:.2f} UBS por 10 mil".replace(",", "."))


# ---------------------------------------------------------------------------
# 05) Análise multivariada: regressão linear múltipla
# ---------------------------------------------------------------------------
def questao_05(dados: pd.DataFrame) -> None:
    titulo("05) Análise multivariada: regressão linear múltipla")
    y = "ubs_10mil"
    xs = ["log10_populacao", "pct_publicos", "pct_internet"]
    variaveis = dados[[y] + xs]

    grade = sns.pairplot(variaveis.rename(columns=CURTOS), diag_kind="hist",
                         plot_kws={"s": 8, "alpha": 0.3, "edgecolor": None}, height=2.2)
    grade.figure.suptitle("Gráfico de Dispersão entre as variáveis", y=1.02)
    grade.savefig(GRAFICOS / "q05a_dispersao.png", dpi=120)
    plt.close("all")

    print("b) Matriz de covariância:")
    print(variaveis.cov().round(4).to_string())
    print("\n   Matriz de correlação de Pearson:")
    print(variaveis.corr().round(4).to_string())

    plt.figure(figsize=(7, 5.5))
    sns.heatmap(variaveis.rename(columns=CURTOS).corr(), annot=True, fmt=".3f",
                cmap="coolwarm", vmin=-1, vmax=1, square=True)
    plt.xticks(rotation=20)
    plt.yticks(rotation=0)
    plt.title("Gráfico de Correlação Linear")
    salvar("q05c_correlacao.png")

    modelo = sm.OLS(dados[y], sm.add_constant(dados[xs])).fit()
    b0, b1, b2, b3 = modelo.params
    print(f"\nd) Equação: UBS por 10 mil = {b0:.4f} + ({b1:.4f}) x log10(população) "
          f"+ ({b2:.4f}) x % públicos + ({b3:.4f}) x % com internet")
    print(f"e) R² = {modelo.rsquared:.4f} | R² ajustado = {modelo.rsquared_adj:.4f} | "
          f"F = {modelo.fvalue:.2f} | p-valor do F = {modelo.f_pvalue:.3e}")
    print(modelo.summary())

    habitantes, publicos, internet = 30_000, 50, 90
    previsto = b0 + b1 * log10(habitantes) + b2 * publicos + b3 * internet
    print(f"f) Município com 30.000 habitantes, {publicos}% de estabelecimentos públicos e "
          f"{internet}% com internet -> {previsto:.2f} UBS por 10 mil")


# ---------------------------------------------------------------------------
# 06) Análise multivariada: regressão logística binária
# ---------------------------------------------------------------------------
def questao_06(dados: pd.DataFrame) -> None:
    titulo("06) Regressão logística binária: o município tem hospital ou pronto atendimento?")
    y = dados["tem_hospital_ou_pa"]
    xs = ["log10_populacao", "ubs_10mil", "estab_10mil"]
    X = sm.add_constant(dados[xs])
    print(f"Municípios com hospital ou pronto atendimento: {y.sum()} de {len(y)} ({100 * y.mean():.1f}%)")

    modelo = sm.Logit(y, X).fit(disp=0)
    b0, b1, b2, b3 = modelo.params
    print(f"a) Equação: P(Y=1) = 1 / (1 + e^-({b0:.4f} + {b1:.4f} x log10(população) "
          f"+ ({b2:.4f}) x UBS por 10 mil + {b3:.4f} x estab. por 10 mil))")
    print(modelo.summary())

    figura, eixos = plt.subplots(1, 3, figsize=(15, 5))
    for eixo, variavel in zip(eixos, xs):
        grade = np.linspace(dados[variavel].min(), dados[variavel].max(), 200)
        novo = pd.DataFrame({"const": 1.0, **{v: dados[v].mean() for v in xs}}, index=range(200))
        novo[variavel] = grade
        eixo.scatter(dados[variavel], y, s=6, alpha=0.15)
        eixo.plot(grade, modelo.predict(novo[["const"] + xs]), color="red", lw=2)
        eixo.set_title(f"Sigmoide: {NOMES[variavel]}", fontsize=12)
        eixo.set_xlabel(NOMES[variavel])
        eixo.set_ylabel("Probabilidade")
    salvar("q06a_sigmoides.png")

    classe = (modelo.predict(X) > 0.5).astype(int)
    matriz = confusion_matrix(y, classe)
    acuracia = accuracy_score(y, classe)
    print("b) Matriz de confusão (linhas = real, colunas = previsto; 0 = não tem, 1 = tem):")
    print(matriz)
    print(f"   Acurácia = {acuracia:.4f} | acurácia de quem chuta sempre 'tem' = {y.mean():.4f}")

    plt.figure(figsize=(6, 4.8))
    sns.heatmap(matriz, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Não tem", "Tem"], yticklabels=["Não tem", "Tem"])
    plt.title(f"Matriz de Confusão (acurácia = {100 * acuracia:.1f}%)")
    plt.xlabel("Previsto pelo modelo")
    plt.ylabel("Real (CNES)")
    salvar("q06b_matriz_confusao.png")

    novos = pd.DataFrame({
        "const": [1.0, 1.0],
        "log10_populacao": [log10(4_000), log10(25_000)],
        "ubs_10mil": [7.0, 4.0],
        "estab_10mil": [20.0, 20.0],
    })
    probabilidades = modelo.predict(novos)
    for habitantes, ubs, p in zip((4_000, 25_000), (7.0, 4.0), probabilidades):
        populacao = f"{habitantes:,}".replace(",", ".")
        print(f"c) Município com {populacao} habitantes, {ubs:.0f} UBS por 10 mil e 20 estab. por 10 mil "
              f"-> P = {p:.4f} -> classe {int(p > 0.5)} ({'tem' if p > 0.5 else 'não tem'})")


def main() -> None:
    GRAFICOS.mkdir(exist_ok=True)
    dados = pd.read_csv(garantir_base(), dtype={"cod_ibge": str, "cod_ibge6": str})
    questao_01(dados)
    questao_02(dados)
    questao_03(dados)
    questao_04(dados)
    questao_05(dados)
    questao_06(dados)
    print(f"\nGráficos salvos em {GRAFICOS.name}/")


if __name__ == "__main__":
    main()
