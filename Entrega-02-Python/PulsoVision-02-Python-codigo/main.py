# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/main.py
# Resumo:  Ponto de entrada da API REST (Flask). Cria a aplicação, registra
#          as rotas de leituras e indicadores, padroniza os erros em JSON e
#          sobe o servidor na porta 5000.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from routes.leituras import indicadores_bp, leituras_bp

PASTA = Path(__file__).resolve().parent


def create_app(config=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    app.config["CSV_LEITURAS"] = PASTA / "dados" / "leituras.csv"
    app.config["MAX_CONTENT_LENGTH"] = 4096
    if config:
        app.config.update(config)

    app.register_blueprint(leituras_bp)
    app.register_blueprint(indicadores_bp)

    @app.get("/")
    def inicio():
        return jsonify({
            "mensagem": "PulsoVision · API de Lotação",
            "rotas": {
                "/leituras": ["GET", "POST"],
                "/indicadores": ["GET"],
            },
        })

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        resposta = erro.get_response()
        resposta.data = app.json.dumps({"erro": erro.description})
        resposta.content_type = "application/json"
        return resposta

    @app.errorhandler(500)
    def erro_interno(erro):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
