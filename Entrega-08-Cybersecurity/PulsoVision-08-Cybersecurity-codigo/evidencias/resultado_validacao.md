# Resultado da validação de segurança (antes × depois)

Gerado em 17/11/2026 10:28 por `validar_seguranca.py`.

| ID | Teste | Risco | Antes | Depois | Resultado |
|---|---|---|---|---|---|
| A01 | Leitura legítima e assinada do totem | funcionalidade | HTTP 201, gravada | HTTP 201, gravada | mitigado |
| A02 | Atacante envia LOTADO falso sem credencial | R01 | HTTP 201, gravada (1 linha nova) | HTTP 401, nada gravado (0 linha nova) | mitigado |
| A03 | Assinatura feita com segredo errado | R01 | HTTP 201 (não há verificação) | HTTP 401 | mitigado |
| A04 | Reenvio (replay) de uma leitura legítima capturada | R03 | HTTP 201 e 201: leitura duplicada | HTTP 201 e 409: segunda recusada | mitigado |
| A05 | Leitura capturada há 10 minutos reenviada | R03 | aceita (não há horário) | HTTP 401 | mitigado |
| A06 | Corpo alterado no caminho (40 pessoas em vez de 1) | R02 | HTTP 201, valor alterado gravado | HTTP 401, alteração detectada | mitigado |
| A07 | Totem da UBS Jardim Paulista tenta informar a UBS Continental | R01 | HTTP 201, gravada | HTTP 403 | mitigado |
| A08 | Fórmula de planilha no nome da unidade (CSV injection) | R08 | fórmula gravada no CSV | nome trocado pelo cadastro CNES; fórmula não gravada | mitigado |
| A09 | 100 requisições seguidas do mesmo IP (flood) | R06 | 100 gravadas, 0 bloqueadas | 0 gravadas, 40 barradas pelo limite (429) após 60 | mitigado |
| A10 | Totem comprometido envia 25 leituras válidas em 1 minuto | R06 | todas aceitas | 16 aceitas, 9 barradas | mitigado |
| A11 | Consulta do histórico detalhado sem login | R07 | HTTP 200, 50 leituras expostas | HTTP 401 sem token; HTTP 200 com token de gestor | mitigado |
| A12 | Gestor tenta ler o log de auditoria (privilégio mínimo) | R07 | HTTP 404: não existe log | gestor HTTP 403; auditor HTTP 200 | mitigado |
| A13 | Indicadores públicos continuam abertos para o app do cidadão | funcionalidade | HTTP 200 | HTTP 200, ranking com 1 unidade(s) | mitigado |
| A14 | Corpo de 1 MB para esgotar memória | R06 | HTTP 413 (limite de 4 KB da API 02) | HTTP 413 (limite mantido) | mitigado |
| A15 | Cabeçalhos de segurança HTTP | R07 | 0 de 6 | 6 de 6 | mitigado |
| A16 | Log de auditoria e detecção de adulteração | R14 | nenhum registro de eventos | 136 eventos; cadeia íntegra = True; após editar 1 linha: íntegra = False (linha 5) | mitigado |
| A17 | IP do usuário no log (dado pessoal) | R09 | sem log | IP guardado só como pseudônimo HMAC | mitigado |
| B01 | Alguém na mesma rede captura a leitura no caminho | R02 | HTTP 201; JSON da lotação visível em texto puro (538 bytes) | HTTP 201; só bytes cifrados (TLSv1.3, TLS_AES_256_GCM_SHA384); conexão HTTP sem TLS recusada | mitigado |
| C01 | Dado pessoal da base bruta do CNES chegando ao projeto | R04 | 640.122 linhas; CPF válidos: 776.078; e-mails: 370.664; telefones: 112.323; 8 colunas pessoais | bases usadas pelos modelos: base_municipios_ml.csv = 0 achados; base_municipios.csv = 0 achados (varredura feita agora) | mitigado |
| C02 | Chaves de nuvem (AWS) ou chave privada esquecidas no repositório | R05 | sem verificação antes do commit | varredura do repositório: 0 arquivo(s) com credencial | mitigado |
| D01 | Relato com CPF, telefone e ordem para a IA baixar a cor | R09/R10 | texto inteiro iria ao modelo (CPF, telefone e a ordem junto) | removidos {'cpf': 1, 'telefone': 1}; manipulação detectada = True; relato vai delimitado como dado | mitigado |
| D02 | Modelo (ou texto manipulado) tenta baixar VERMELHO para VERDE | R10 | regra já existia no desenho da triagem (RN, seção 8.2) | cor final = VERMELHO | mitigado |
| D03 | Foto do celular com localização GPS no EXIF | R09 | GPS presente na foto enviada = True (endereço da pessoa) | foto aceita = True; GPS na cópia que vai à CNN = False | mitigado |
| D04 | Fotos sem qualidade ou arquivo falso | R10/R12 | a CNN pontuaria qualquer arquivo que abrisse | escura: foto escura demais; procure um lugar iluminado; borrada: foto borrada; segure firme e foque na lesão; pequena: resolução baixa (120×120); aproxime a câmera; não é imagem: arquivo não é uma imagem válida | mitigado |
| D05 | Bomba de descompressão: PNG de 7 KB com 64 milhões de pixels | R06 | Pillow padrão abre (8000×8000) | imagem grande demais (possível bomba de descompressão) | mitigado |
| D06 | Resposta gerada com diagnóstico ou falsa tranquilização | R11 | exibida ao cidadão como veio | 2 de 2 inadequadas bloqueadas; a adequada passou = True | mitigado |
| D07 | Pontuação da CNN perto do corte (0,36 com corte 0,335) | R12 | decisão automática | revisão humana = True (pontuação 0.360 perto do corte 0.335); pontuação 0,91 = False | mitigado |
| D08 | Arquivo do modelo trocado por um pickle malicioso | R13 | joblib.load executou código do atacante = True | modelo legítimo carregou (Regressão Logística ajustada); adulterado bloqueado = True; código executado = False | mitigado |

**28 de 28 verificações passaram.**
