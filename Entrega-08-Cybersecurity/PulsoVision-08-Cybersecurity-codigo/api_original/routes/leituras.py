# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_original/routes/leituras.py
# Resumo:  Cópia da API da disciplina 02, sem nenhuma alteração no código: é o
#          "antes" da validação de segurança.
#          Rotas da API: POST /leituras recebe e valida a leitura do totem,
#          GET /leituras consulta o histórico com filtros (cnes, status,
#          limite) e GET /indicadores devolve os indicadores calculados.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

from flask import Blueprint, abort, current_app, jsonify, request

from models.leitura import VALORES_PERMITIDOS, validar
from services.leituras import RepositorioCSV, calcular_indicadores, filtrar, processar

leituras_bp = Blueprint("leituras", __name__, url_prefix="/leituras")
indicadores_bp = Blueprint("indicadores", __name__, url_prefix="/indicadores")

LIMITE_PADRAO = 50
LIMITE_MAXIMO = 500


def get_repositorio():
    return RepositorioCSV(current_app.config["CSV_LEITURAS"])


def ler_leitura():
    if not request.is_json:
        abort(415, description="Envie o corpo com Content-Type: application/json.")
    leitura = request.get_json(silent=True)
    if leitura is None:
        abort(400, description="O corpo não é um JSON válido.")
    return leitura


def ler_limite():
    texto = request.args.get("limite", str(LIMITE_PADRAO))
    if not texto.isdigit() or not 1 <= int(texto) <= LIMITE_MAXIMO:
        abort(400, description=f"limite deve ser um número entre 1 e {LIMITE_MAXIMO}.")
    return int(texto)


@leituras_bp.post("")
def receber_leitura():
    leitura = ler_leitura()
    erros = validar(leitura)
    if erros:
        return jsonify({"erro": "Leitura fora do contrato v1.0.", "detalhes": erros}), 400

    registro = processar(leitura)
    get_repositorio().salvar(registro)
    return jsonify(registro), 201


@leituras_bp.get("")
def listar_leituras():
    status = request.args.get("status")
    if status and status not in VALORES_PERMITIDOS["status"]:
        abort(400, description="status deve ser OK, ALERTA, LOTADO ou SEM_LEITURA.")

    registros = filtrar(
        get_repositorio().listar(),
        cnes=request.args.get("cnes"),
        status=status,
        limite=ler_limite(),
    )
    return jsonify({"quantidade": len(registros), "leituras": registros})


@indicadores_bp.get("")
def indicadores():
    return jsonify(calcular_indicadores(get_repositorio().listar()))
