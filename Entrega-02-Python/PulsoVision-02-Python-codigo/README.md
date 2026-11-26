# 02 · Computational Thinking with Python — API de Lotação

A API REST (Flask) recebe as leituras do totem, valida o contrato v1.0, aplica as mesmas regras do `Regras.h`,
grava o histórico em CSV e devolve indicadores de lotação por unidade.

| Rota | O que faz |
|---|---|
| `POST /leituras` | Recebe e valida uma leitura JSON, classifica e grava em `dados/leituras.csv` |
| `GET /leituras` | Lista o histórico (com `?limite=`) |
| `GET /indicadores` | Total de leituras por status, % de LOTADO, média de pessoas aguardando e ranking das unidades |

## Como rodar
```bash
pip install -r requirements-dev.txt
pytest testes                 # 11 testes automatizados
python main.py                # sobe a API em http://127.0.0.1:5000
python cenarios.py            # em outro terminal: os 3 cenários de teste
python importar_totem.py      # envia as leituras reais do totem (dados_totem/dados.csv)
```

`totem-http/` é o mesmo firmware do totem da disciplina 01, agora enviando `POST /leituras` por HTTP.
O PDF `Python - Entrega PulsoVision API de Lotacao.pdf` traz os prints dos testes.
