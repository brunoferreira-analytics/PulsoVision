# PulsoVision · API de Lotação
# Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
#
# Arquivo: 02-python-api/testes/test_api.py
# Resumo:  Testes automatizados dos endpoints: os três cenários da entrega, a
#          correção de um totem divergente, as recusas de entrada inválida,
#          os filtros do GET e os indicadores.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

def linhas_csv(caminho):
    if not caminho.exists():
        return 0
    return len(caminho.read_text(encoding="utf-8").strip().splitlines()) - 1


def test_inicio_lista_rotas(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "/leituras" in resposta.get_json()["rotas"]


def test_cenario_1_leitura_ok_e_gravada(client, leitura, csv_teste):
    resposta = client.post("/leituras", json=leitura)
    corpo = resposta.get_json()
    assert resposta.status_code == 201
    assert corpo["status_final"] == "OK"
    assert corpo["confere_totem"] is True
    assert corpo["recomendacao"].startswith("Fila curta")
    assert "data_hora" in corpo
    assert linhas_csv(csv_teste) == 1


def test_cenario_2_fila_parada_vira_lotado(client, leitura, csv_teste):
    leitura.update(fila_distancia_cm=200.0, fila_status="MEDIA", movimento_status="SEM_FLUXO",
                   pessoas_aguardando=3, status="LOTADO", motivo="FILA_PARADA")
    corpo = client.post("/leituras", json=leitura).get_json()
    assert corpo["status_final"] == "LOTADO"
    assert corpo["motivo_api"] == "FILA_PARADA"
    assert corpo["recomendacao"].startswith("Unidade lotada")
    assert linhas_csv(csv_teste) == 1


def test_cenario_3_leitura_invalida_nao_e_gravada(client, leitura, csv_teste):
    del leitura["status"]
    leitura["pessoas_aguardando"] = "muitas"
    resposta = client.post("/leituras", json=leitura)
    corpo = resposta.get_json()
    assert resposta.status_code == 400
    assert "campo ausente: status" in corpo["detalhes"]
    assert "tipo inválido em pessoas_aguardando" in corpo["detalhes"]
    assert linhas_csv(csv_teste) == 0


def test_api_corrige_totem_divergente(client, leitura):
    leitura.update(fila_distancia_cm=80.0)
    corpo = client.post("/leituras", json=leitura).get_json()
    assert corpo["status_api"] == "LOTADO"
    assert corpo["confere_totem"] is False
    assert corpo["status_final"] == "LOTADO"


def test_rejeita_corpo_que_nao_e_json(client):
    resposta = client.post("/leituras", data="texto", content_type="text/plain")
    assert resposta.status_code == 415


def test_rejeita_json_quebrado(client):
    resposta = client.post("/leituras", data='{"status": "OK"', content_type="application/json")
    assert resposta.status_code == 400


def test_rejeita_campo_fora_do_contrato(client, leitura):
    leitura["comando"] = "apagar_tudo"
    resposta = client.post("/leituras", json=leitura)
    assert resposta.status_code == 400
    assert "campo fora do contrato: comando" in resposta.get_json()["detalhes"]


def test_rejeita_mensagem_gigante(client):
    resposta = client.post("/leituras", data='{"x": "' + "A" * 6000 + '"}', content_type="application/json")
    assert resposta.status_code == 413


def test_get_filtra_por_status_e_limite(client, leitura):
    client.post("/leituras", json=leitura)
    leitura.update(id_leitura=2, fila_distancia_cm=80.0, fila_status="LONGA", pessoas_aguardando=5,
                   status="LOTADO", motivo="FILA_LONGA")
    client.post("/leituras", json=leitura)

    corpo = client.get("/leituras?status=LOTADO").get_json()
    assert corpo["quantidade"] == 1
    assert corpo["leituras"][0]["id_leitura"] == 2

    assert client.get("/leituras?limite=1").get_json()["quantidade"] == 1
    assert client.get("/leituras?limite=0").status_code == 400
    assert client.get("/leituras?status=CHEIO").status_code == 400


def test_indicadores(client, leitura):
    client.post("/leituras", json=leitura)
    leitura.update(id_leitura=2, fila_distancia_cm=80.0, fila_status="LONGA", pessoas_aguardando=5,
                   status="LOTADO", motivo="FILA_LONGA")
    client.post("/leituras", json=leitura)

    corpo = client.get("/indicadores").get_json()
    geral = corpo["geral"]
    assert geral["total_leituras"] == 2
    assert geral["media_pessoas_aguardando"] == 2.5
    assert geral["max_pessoas_aguardando"] == 5
    assert geral["percentual_lotado"] == 50.0
    assert corpo["ranking_unidades"][0]["situacao_atual"] == "LOTADO"
