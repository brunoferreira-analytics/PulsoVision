# 08 · Cognitive Cybersecurity — a blindagem do PulsoVision

> "A porta de entrada da saúde pra quem não tem médico."

**Resultado:** 14 riscos mapeados (7 críticos), medidas implementadas na API, nas bases e nos componentes de IA,
e **28 de 28 verificações antes × depois** aprovadas. Nenhum risco ficou crítico ou alto.

Integrantes: Tiago Thomaz Cesaro · Bruno Henrique Ferreira Ambrosio · Lucas Maximo dos Santos

## Como rodar (3 minutos)

```bash
pip install -r requirements.txt
python validar_seguranca.py          # roda todos os ataques controlados e grava evidencias/
python gerar_matriz_riscos.py        # matriz probabilidade × impacto, antes e depois
```

> **Sobre a verificação C01:** ela varre a base bruta do CNES, que **não vai na entrega** por conter CPF,
> e-mail e telefone. Para rodá-la, aponte o arquivo:
> `python validar_seguranca.py --cnes <caminho do tbEstabelecimento202609.csv>` → **28 de 28**.
> Sem a base bruta, o script mostra a C01 como pulada e conclui **27 de 27**.

Demonstração da API segura ao vivo (para o vídeo):

```bash
cd api_segura
python gerar_segredos.py                         # mostra os segredos UMA vez; não grave a tela neste passo
python executar.py --https                       # sobe em https://127.0.0.1:5443
python totem_simulado.py --segredo <segredo>     # em outro terminal: leitura assinada -> 201
curl --cacert certs/pulso.crt https://127.0.0.1:5443/leituras      # sem token -> 401
curl http://127.0.0.1:5443/indicadores                             # sem TLS -> recusado
```

> No **Windows (PowerShell)**, use `curl.exe` em vez de `curl`: no PowerShell, `curl` é outro comando.

Varredura LGPD (também serve como verificação antes do commit):

```bash
python privacidade/varredura_dados_sensiveis.py ../ --falhar
```

## O que tem em cada pasta

| Pasta / arquivo | Conteúdo |
|---|---|
| `api_original/` | Cópia da API da disciplina 02, sem alteração: é o **antes** |
| `api_segura/` | A mesma API com a camada de segurança: HMAC por totem, anti-replay, vínculo totem↔CNES, perfis, limite de taxa, auditoria encadeada, cabeçalhos, HTTPS |
| `privacidade/` | Varredura de CPF, e-mail, telefone, chaves AWS e chaves privadas (nunca imprime os valores) |
| `ia/` | Guardrails: relato sem dado pessoal e com detecção de manipulação, foto validada e sem EXIF/GPS, filtro de resposta, cor que só sobe, revisão humana, carga de modelo só com SHA-256 conferido |
| `riscos.json` | Os 14 riscos com probabilidade e impacto, antes e depois |
| `validar_seguranca.py` | Os 28 testes antes × depois |
| `evidencias/` | Resultados gerados: tabela, saída do terminal, log de auditoria de exemplo, matriz de riscos, varredura das bases |

## Regras de segurança do grupo

- Segredos, certificados e logs **nunca** vão para o Git (ver `.gitignore`).
- A base bruta do CNES (`tbEstabelecimento*.csv`) tem CPF, e-mail e telefone: fica só na máquina de quem processa.
- Não gravar a aba "AWS Details" do Learner Lab nem a saída de `gerar_segredos.py` no vídeo.
- Os testes só rodam no ambiente do próprio projeto.

Documento completo (contexto, matriz, arquitetura, medidas, IA, validação e evolução): ver o PDF da entrega.
