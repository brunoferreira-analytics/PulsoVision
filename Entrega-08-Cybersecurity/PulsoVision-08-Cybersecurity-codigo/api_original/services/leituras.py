# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_original/services/leituras.py
# Resumo:  Cópia da API da disciplina 02, sem nenhuma alteração no código: é o
#          "antes" da validação de segurança.
#          Regras de negócio: reclassifica cada leitura com a mesma regra do
#          totem, fica com o status mais grave, gera a recomendação ao
#          cidadão, grava o histórico em CSV e calcula os indicadores por
#          unidade.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import csv
import threading
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LIMIAR_FILA_MEDIA_CM = 250.0
LIMIAR_FILA_LONGA_CM = 120.0
DISTANCIA_MIN_VALIDA_CM = 2.0
DISTANCIA_MAX_VALIDA_CM = 450.0

GRAVIDADE = {"OK": 0, "SEM_LEITURA": 1, "ALERTA": 2, "LOTADO": 3}

RECOMENDACOES = {
    "OK": "Fila curta: pode ir a esta unidade.",
    "ALERTA": "Fila moderada: espere um pouco ou considere outra unidade.",
    "LOTADO": "Unidade lotada: procure outra unidade próxima.",
    "SEM_LEITURA": "Sem informação de lotação no momento.",
}

CAMPOS_CSV = [
    "data_hora", "versao_contrato", "id_leitura", "id_totem", "cnes", "nome_unidade",
    "tipo_unidade", "cod_municipio", "fila_distancia_cm", "fila_status", "movimento",
    "movimento_status", "pessoas_aguardando", "status", "motivo",
    "status_api", "motivo_api", "confere_totem", "status_final", "recomendacao",
]

CAMPOS_INTEIROS = {"id_leitura", "pessoas_aguardando"}
CAMPOS_DECIMAIS = {"fila_distancia_cm"}
CAMPOS_BOOLEANOS = {"movimento", "confere_totem"}


def classificar_fila(distancia_cm):
    if not DISTANCIA_MIN_VALIDA_CM <= distancia_cm <= DISTANCIA_MAX_VALIDA_CM:
        return "SEM_LEITURA"
    if distancia_cm <= LIMIAR_FILA_LONGA_CM:
        return "LONGA"
    if distancia_cm <= LIMIAR_FILA_MEDIA_CM:
        return "MEDIA"
    return "CURTA"


def decidir_status(fila_status, movimento_status):
    if fila_status == "SEM_LEITURA":
        return "SEM_LEITURA", "SENSOR_SEM_ECO"
    if fila_status == "LONGA":
        return "LOTADO", "FILA_LONGA"
    if fila_status == "MEDIA":
        if movimento_status == "SEM_FLUXO":
            return "LOTADO", "FILA_PARADA"
        return "ALERTA", "FILA_MEDIA"
    return "OK", "FILA_CURTA"


def processar(leitura):
    """Confere a decisão do totem com a mesma regra e fica com a mais grave."""
    fila_status = classificar_fila(leitura["fila_distancia_cm"])
    status_api, motivo_api = decidir_status(fila_status, leitura["movimento_status"])

    status_final = max(leitura["status"], status_api, key=GRAVIDADE.get)

    return {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **leitura,
        "status_api": status_api,
        "motivo_api": motivo_api,
        "confere_totem": status_api == leitura["status"],
        "status_final": status_final,
        "recomendacao": RECOMENDACOES[status_final],
    }


def converter_linha(linha):
    registro = dict(linha)
    for campo in CAMPOS_INTEIROS:
        registro[campo] = int(registro[campo])
    for campo in CAMPOS_DECIMAIS:
        registro[campo] = float(registro[campo])
    for campo in CAMPOS_BOOLEANOS:
        registro[campo] = registro[campo] == "true"
    return registro


class RepositorioCSV:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.trava = threading.Lock()

    def salvar(self, registro):
        linha = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in registro.items()}
        with self.trava:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            novo = not self.caminho.exists()
            with self.caminho.open("a", newline="", encoding="utf-8") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV)
                if novo:
                    escritor.writeheader()
                escritor.writerow(linha)

    def listar(self):
        if not self.caminho.exists():
            return []
        with self.trava, self.caminho.open(newline="", encoding="utf-8") as arquivo:
            return [converter_linha(linha) for linha in csv.DictReader(arquivo)]


def filtrar(registros, cnes=None, status=None, limite=50):
    selecionados = []
    for registro in reversed(registros):
        if cnes and registro["cnes"] != cnes:
            continue
        if status and registro["status_final"] != status:
            continue
        selecionados.append(registro)
        if len(selecionados) == limite:
            break
    return selecionados


def resumir(registros):
    total = len(registros)
    por_status = Counter(r["status_final"] for r in registros)
    pessoas = [r["pessoas_aguardando"] for r in registros]
    return {
        "total_leituras": total,
        "por_status": {s: por_status.get(s, 0) for s in GRAVIDADE},
        "media_pessoas_aguardando": round(sum(pessoas) / total, 2) if total else 0,
        "max_pessoas_aguardando": max(pessoas, default=0),
        "percentual_lotado": round(100 * por_status.get("LOTADO", 0) / total, 1) if total else 0,
        "divergencias_totem_api": sum(1 for r in registros if not r["confere_totem"]),
    }


def calcular_indicadores(registros):
    por_unidade = defaultdict(list)
    for registro in registros:
        por_unidade[registro["cnes"]].append(registro)

    unidades = []
    for cnes, lista in por_unidade.items():
        ultima = lista[-1]
        unidades.append({
            "cnes": cnes,
            "nome_unidade": ultima["nome_unidade"],
            "tipo_unidade": ultima["tipo_unidade"],
            "situacao_atual": ultima["status_final"],
            "pessoas_agora": ultima["pessoas_aguardando"],
            "recomendacao": ultima["recomendacao"],
            "ultima_leitura": ultima["data_hora"],
            **resumir(lista),
        })

    unidades.sort(key=lambda u: (GRAVIDADE[u["situacao_atual"]], u["media_pessoas_aguardando"]))

    return {"geral": resumir(registros), "ranking_unidades": unidades}
