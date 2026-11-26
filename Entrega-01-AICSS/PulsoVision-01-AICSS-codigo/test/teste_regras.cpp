/*
 * PulsoVision · Totem de Lotação
 * Disciplina 01: AI Computer Systems & Sensors (AICSS) · Global Solution 2026.2 — FIAP
 *
 * Arquivo: 01-aicss-totem/test/teste_regras.cpp
 * Resumo:  Testes automatizados das regras de decisão do totem: limiares
 *          da fila, estimativa de pessoas, janela do PIR e decisão
 *          combinada dos dois sensores.
 *
 * Integrantes:
 *   - Tiago Thomaz Cesaro
 *   - Bruno Henrique Ferreira Ambrosio
 *   - Lucas Maximo dos Santos
 */

#include <cstdio>
#include <cstring>
#include "Regras.h"

static int falhas = 0;

static void confere(bool ok, const char* descricao) {
  std::printf("[%s] %s\n", ok ? " OK " : "FALHOU", descricao);
  if (!ok) falhas++;
}

static bool igual(const char* a, const char* b) { return std::strcmp(a, b) == 0; }

int main() {
  using namespace Regras;
  const char* motivo = "";

  std::printf("-- Sensor 1: fila (ultrassonico)\n");
  confere(igual(classificarFila(400.0f), "CURTA"), "400 cm -> CURTA");
  confere(igual(classificarFila(250.1f), "CURTA"), "250,1 cm -> CURTA (logo acima do limiar)");
  confere(igual(classificarFila(250.0f), "MEDIA"), "250 cm -> MEDIA (limiar)");
  confere(igual(classificarFila(120.1f), "MEDIA"), "120,1 cm -> MEDIA");
  confere(igual(classificarFila(120.0f), "LONGA"), "120 cm -> LONGA (limiar)");
  confere(igual(classificarFila(0.0f), "SEM_LEITURA"), "0 cm (sem eco) -> SEM_LEITURA, nunca LOTADO");
  confere(igual(classificarFila(500.0f), "SEM_LEITURA"), "500 cm (fora do alcance) -> SEM_LEITURA");

  std::printf("-- Estimativa de pessoas (60 cm por pessoa, area de 400 cm)\n");
  confere(estimarPessoas(400.0f) == 0, "400 cm -> 0 pessoas");
  confere(estimarPessoas(403.5f) == 0, "403,5 cm -> 0 pessoas (leitura do Wokwi no maximo)");
  confere(estimarPessoas(200.0f) == 3, "200 cm -> 3 pessoas");
  confere(estimarPessoas(80.0f) == 5, "80 cm -> 5 pessoas");
  confere(estimarPessoas(21.0f) == 6, "21 cm -> 6 pessoas");
  confere(estimarPessoas(0.0f) == 0, "sem eco -> 0 (status SEM_LEITURA avisa)");

  std::printf("-- Sensor 2: movimento (PIR)\n");
  confere(!semFluxo(29999, 0), "29,9 s sem movimento -> ainda FLUXO");
  confere(semFluxo(30000, 0), "30 s sem movimento -> SEM_FLUXO");
  confere(igual(classificarMovimento(true), "SEM_FLUXO"), "rotulo SEM_FLUXO");

  std::printf("-- Decisao combinada\n");
  confere(igual(decidirStatus("CURTA", true, &motivo), "OK") && igual(motivo, "FILA_CURTA"),
          "fila curta -> OK (PIR nao importa)");
  confere(igual(decidirStatus("MEDIA", false, &motivo), "ALERTA") && igual(motivo, "FILA_MEDIA"),
          "fila media andando -> ALERTA");
  confere(igual(decidirStatus("MEDIA", true, &motivo), "LOTADO") && igual(motivo, "FILA_PARADA"),
          "fila media parada -> LOTADO (vies pro-seguranca)");
  confere(igual(decidirStatus("LONGA", false, &motivo), "LOTADO") && igual(motivo, "FILA_LONGA"),
          "fila longa -> LOTADO");
  confere(igual(decidirStatus("SEM_LEITURA", false, &motivo), "SEM_LEITURA") && igual(motivo, "SENSOR_SEM_ECO"),
          "sem leitura -> SEM_LEITURA");

  std::printf("\n%s (%d falha(s))\n", falhas == 0 ? "TODOS OS TESTES PASSARAM" : "HA FALHAS", falhas);
  return falhas == 0 ? 0 : 1;
}
