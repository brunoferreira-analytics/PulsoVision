/*
 * PulsoVision · Totem de Lotação
 * Disciplina 01: AI Computer Systems & Sensors (AICSS) · Global Solution 2026.2 — FIAP
 *
 * Arquivo: 01-aicss-totem/src/Regras.h
 * Resumo:  Regras de decisão do totem (C++ puro, testável). Classifica
 *          a fila pela distância, estima as pessoas, avalia o movimento
 *          do PIR e combina os dois sensores no status final + motivo.
 *
 * Integrantes:
 *   - Tiago Thomaz Cesaro
 *   - Bruno Henrique Ferreira Ambrosio
 *   - Lucas Maximo dos Santos
 */

#pragma once
#include <string.h>

namespace Regras {

  const float COMPRIMENTO_AREA_CM     = 400.0;
  const float ESPACO_POR_PESSOA_CM    = 60.0;
  const float LIMIAR_FILA_MEDIA_CM    = 250.0;
  const float LIMIAR_FILA_LONGA_CM    = 120.0;
  const float DISTANCIA_MIN_VALIDA_CM = 2.0;
  const float DISTANCIA_MAX_VALIDA_CM = 450.0;
  const unsigned long JANELA_SEM_FLUXO_MS = 30000;

  inline bool leituraValida(float distanciaCm) {
    return distanciaCm >= DISTANCIA_MIN_VALIDA_CM &&
           distanciaCm <= DISTANCIA_MAX_VALIDA_CM;
  }

  inline const char* classificarFila(float distanciaCm) {
    if (!leituraValida(distanciaCm)) return "SEM_LEITURA";
    if (distanciaCm <= LIMIAR_FILA_LONGA_CM) return "LONGA";
    if (distanciaCm <= LIMIAR_FILA_MEDIA_CM) return "MEDIA";
    return "CURTA";
  }

  inline int estimarPessoas(float distanciaCm) {
    if (!leituraValida(distanciaCm)) return 0;
    float d = distanciaCm > COMPRIMENTO_AREA_CM ? COMPRIMENTO_AREA_CM : distanciaCm;
    return (int)((COMPRIMENTO_AREA_CM - d) / ESPACO_POR_PESSOA_CM + 0.5f);
  }

  inline bool semFluxo(unsigned long agoraMs, unsigned long ultimoMovimentoMs) {
    return (agoraMs - ultimoMovimentoMs) >= JANELA_SEM_FLUXO_MS;
  }

  inline const char* classificarMovimento(bool estaSemFluxo) {
    return estaSemFluxo ? "SEM_FLUXO" : "FLUXO";
  }

  // Fila média sem movimento sobe para LOTADO (viés pró-segurança).
  inline const char* decidirStatus(const char* filaStatus, bool estaSemFluxo,
                                   const char** motivo) {
    if (strcmp(filaStatus, "SEM_LEITURA") == 0) { *motivo = "SENSOR_SEM_ECO"; return "SEM_LEITURA"; }
    if (strcmp(filaStatus, "LONGA") == 0)       { *motivo = "FILA_LONGA";     return "LOTADO"; }
    if (strcmp(filaStatus, "MEDIA") == 0) {
      if (estaSemFluxo) { *motivo = "FILA_PARADA"; return "LOTADO"; }
      *motivo = "FILA_MEDIA";
      return "ALERTA";
    }
    *motivo = "FILA_CURTA";
    return "OK";
  }
}
