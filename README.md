# PulsoVision

**A porta de entrada da saúde pra quem não tem médico.**

Global Solution 2026.2 · CitizenTech · FIAP · Turma 1TIAPY

O PulsoVision junta três sinais para orientar o cidadão sobre para onde ir:
- o que a pessoa conta, numa triagem por cores que não dá diagnóstico;
- a foto de uma lesão de pele, avaliada por uma rede neural;
- a lotação real das UBS, medida por um totem ESP32.

Cruzando CNES e IBGE, o projeto encontrou 1.595 municípios brasileiros sem nenhuma unidade de urgência. O trabalho se liga às ODS 3 (saúde e bem-estar) e 10 (redução das desigualdades).

## Vídeo final

[youtu.be/_ICunJJjr64](https://youtu.be/_ICunJJjr64)

## Entregas por disciplina

| Pasta | Disciplina | O que tem |
|---|---|---|
| [`Entrega-01-AICSS`](Entrega-01-AICSS) | AI Computer Systems & Sensors | Totem ESP32 (HC-SR04 + PIR) no Wokwi, servidor socket, testes das regras e PDF |
| [`Entrega-02-Python`](Entrega-02-Python) | Computational Thinking with Python | API Flask de lotação (POST/GET, CSV, indicadores), 11 testes e PDF |
| [`Entrega-03-Datascience`](Entrega-03-Datascience) | Cognitive Data Science (Databricks) | Medalhão bronze → silver → gold, em PDF |
| [`Entrega-04-AWS`](Entrega-04-AWS) | Plataformas e Serviços Cognitivos (AWS) | Medalhão com S3, Glue e Athena, em PDF |
| [`Entrega-05-Estatistica`](Entrega-05-Estatistica) | Statistical Computing with R & Python | Base CNES + IBGE (5.571 municípios), scripts Python e relatório |
| [`Entrega-06-Machine-Learning`](Entrega-06-Machine-Learning) | Machine Learning & Modelling | Modelo de vazio de urgência (ROC-AUC 0,91), notebook e slides |
| [`Entrega-07-Redes-Neurais`](Entrega-07-Redes-Neurais) | Redes Neurais, Deep Learning e Algoritmos Genéticos | CNN MobileNetV2 na PAD-UFES-20 (AUC 0,90 na validação) e notebook |
| [`Entrega-08-Cybersecurity`](Entrega-08-Cybersecurity) | Cognitive Cybersecurity | 14 riscos, API segura, varredura LGPD, guardrails de IA (28 de 28 verificações) e PDF |
| [`Entrega-09-AI-Challenges`](Entrega-09-AI-Challenges) | AI Challenge | Capa com o link do vídeo final |

## Minha contribuição

Conduzi a maior parte do desenvolvimento técnico do projeto, com apoio de IA generativa:

- modelo de ML de vazio de urgência nos municípios (ROC-AUC de 0,91), com GridSearchCV e validação estratificada;
- CNN com transfer learning (MobileNetV2) para priorizar lesões de pele (AUC de 0,90 na validação);
- guardrails de IA: limpeza de dados pessoais, detecção de prompt injection, filtro de saída, revisão humana e verificação de hash do modelo;
- arquitetura medalhão no Databricks e na AWS (S3, Glue, Athena);
- API Flask de lotação com testes automatizados e integração com o totem ESP32.

## Integrantes

- Tiago Thomaz Cesaro
- Bruno Henrique Ferreira Ambrosio
- Lucas Maximo dos Santos

## Privacidade

Por causa da LGPD, os dados brutos do CNES, que têm CPF, e-mail e telefone, **não estão neste repositório**. Ficaram só as bases agregadas por município.
