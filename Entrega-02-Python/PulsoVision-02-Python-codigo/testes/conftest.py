# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/testes/conftest.py
# Resumo:  Configuração dos testes: cria a aplicação com um CSV temporário e
#          uma leitura válida de exemplo.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import create_app  # noqa: E402


@pytest.fixture
def csv_teste(tmp_path):
    return tmp_path / "leituras.csv"


@pytest.fixture
def client(csv_teste):
    app = create_app({"TESTING": True, "CSV_LEITURAS": csv_teste})
    return app.test_client()


@pytest.fixture
def leitura():
    return {
        "versao_contrato": "1.0",
        "id_leitura": 1,
        "id_totem": "TOTEM-4048296-01",
        "cnes": "4048296",
        "nome_unidade": "UBS Jardim Paulista",
        "tipo_unidade": "UBS",
        "cod_municipio": "351880",
        "fila_distancia_cm": 403.5,
        "fila_status": "CURTA",
        "movimento": False,
        "movimento_status": "FLUXO",
        "pessoas_aguardando": 0,
        "status": "OK",
        "motivo": "FILA_CURTA",
    }
