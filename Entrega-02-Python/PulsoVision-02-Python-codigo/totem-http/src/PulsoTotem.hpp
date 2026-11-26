/*
 * PulsoVision · Totem de Lotação
 * Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
 *
 * Arquivo: 02-python-api/totem-http/src/PulsoTotem.hpp
 * Resumo:  Componentes do totem em namespaces: sensores, LEDs e Wi-Fi iguais
 *          aos do AICSS. O envio agora é um POST HTTP para a API (/leituras),
 *          e a resposta da API aparece no monitor serial.
 *
 * Integrantes:
 *   - Tiago Thomaz Cesaro
 *   - Bruno Henrique Ferreira Ambrosio
 *   - Lucas Maximo dos Santos
 */

#pragma once

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "Regras.h"

const int PIN_TRIG         = 5;
const int PIN_ECHO         = 18;
const int PIN_PIR          = 19;
const int PIN_LED_VERDE    = 25;
const int PIN_LED_AMARELO  = 26;
const int PIN_LED_VERMELHO = 27;

// Unidade real do CNES (DataSUS, set/2026)
namespace Unidade {
  const char* ID_TOTEM      = "TOTEM-4048296-01";
  const char* CNES          = "4048296";
  const char* NOME          = "UBS Jardim Paulista";
  const char* TIPO          = "UBS";
  const char* COD_MUNICIPIO = "351880";
}

struct Leitura {
  int id;
  float filaDistanciaCm;
  const char* filaStatus;
  bool movimento;
  const char* movimentoStatus;
  int pessoasAguardando;
  const char* status;
  const char* motivo;
};

namespace Fila {
  const unsigned long TIMEOUT_ECO_US = 26000;

  void iniciar() {
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_ECHO, INPUT);
  }

  float ler() {
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);
    unsigned long duracao = pulseIn(PIN_ECHO, HIGH, TIMEOUT_ECO_US);
    return duracao * 0.0343 / 2.0;
  }

  const char* avaliar(float distanciaCm) {
    return Regras::classificarFila(distanciaCm);
  }
}

namespace Movimento {
  unsigned long ultimoMovimentoMs = 0;

  void iniciar() {
    pinMode(PIN_PIR, INPUT);
    ultimoMovimentoMs = millis();
  }

  bool ler() {
    bool detectado = digitalRead(PIN_PIR) == HIGH;
    if (detectado) ultimoMovimentoMs = millis();
    return detectado;
  }

  bool semFluxo() {
    return Regras::semFluxo(millis(), ultimoMovimentoMs);
  }

  const char* avaliar() {
    return Regras::classificarMovimento(semFluxo());
  }
}

namespace Sinalizacao {
  const char* statusAtual = "OK";
  const unsigned long PISCA_MS = 400;

  void iniciar() {
    pinMode(PIN_LED_VERDE, OUTPUT);
    pinMode(PIN_LED_AMARELO, OUTPUT);
    pinMode(PIN_LED_VERMELHO, OUTPUT);
  }

  void definir(const char* status) {
    statusAtual = status;
  }

  void atualizar() {
    bool verde = false, amarelo = false, vermelho = false;

    if (strcmp(statusAtual, "OK") == 0) {
      verde = true;
    } else if (strcmp(statusAtual, "ALERTA") == 0) {
      amarelo = true;
    } else if (strcmp(statusAtual, "SEM_LEITURA") == 0) {
      vermelho = (millis() / PISCA_MS) % 2 == 0;
    } else {
      vermelho = true;  // LOTADO ou status desconhecido
    }

    digitalWrite(PIN_LED_VERDE, verde ? HIGH : LOW);
    digitalWrite(PIN_LED_AMARELO, amarelo ? HIGH : LOW);
    digitalWrite(PIN_LED_VERMELHO, vermelho ? HIGH : LOW);
  }
}

namespace Conexao {
  const char* WIFI_SSID = "Wokwi-GUEST";
  const char* WIFI_PASSWORD = "";
  const uint8_t WIFI_CHANNEL = 6;
  const unsigned long TIMEOUT_CONEXAO_MS = 10000;
  const unsigned long INTERVALO_RECONEXAO_MS = 10000;
  unsigned long ultimaTentativaMs = 0;

  void conectar() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD, WIFI_CHANNEL);
    Serial.print("Conectando ao Wi-Fi");
    unsigned long inicio = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - inicio < TIMEOUT_CONEXAO_MS) {
      delay(250);
      Serial.print(".");
    }
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("Wi-Fi conectado! IP do ESP32: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println("Sem Wi-Fi - seguindo offline (sensores e LEDs continuam funcionando).");
    }
    ultimaTentativaMs = millis();
  }

  bool conectado() {
    return WiFi.status() == WL_CONNECTED;
  }

  void manter() {
    if (!conectado() && millis() - ultimaTentativaMs >= INTERVALO_RECONEXAO_MS) {
      ultimaTentativaMs = millis();
      Serial.println("Wi-Fi caiu - tentando reconectar...");
      WiFi.reconnect();
    }
  }
}

namespace Envio {
  const char* URL_API = "http://host.wokwi.internal:5000/leituras";
  const uint16_t TIMEOUT_MS = 3000;
  const char* VERSAO_CONTRATO = "1.0";

  String montarJson(const Leitura& l) {
    JsonDocument doc;
    doc["versao_contrato"]    = VERSAO_CONTRATO;
    doc["id_leitura"]         = l.id;
    doc["id_totem"]           = Unidade::ID_TOTEM;
    doc["cnes"]               = Unidade::CNES;
    doc["nome_unidade"]       = Unidade::NOME;
    doc["tipo_unidade"]       = Unidade::TIPO;
    doc["cod_municipio"]      = Unidade::COD_MUNICIPIO;
    doc["fila_distancia_cm"]  = serialized(String(l.filaDistanciaCm, 1));
    doc["fila_status"]        = l.filaStatus;
    doc["movimento"]          = l.movimento;
    doc["movimento_status"]   = l.movimentoStatus;
    doc["pessoas_aguardando"] = l.pessoasAguardando;
    doc["status"]             = l.status;
    doc["motivo"]             = l.motivo;

    String json;
    serializeJson(doc, json);
    return json;
  }

  bool enviar(const String& json) {
    if (!Conexao::conectado()) {
      Serial.println("Sem Wi-Fi (leitura mantida só no alerta local): " + json);
      return false;
    }

    HTTPClient http;
    http.begin(URL_API);
    http.setConnectTimeout(TIMEOUT_MS);
    http.setTimeout(TIMEOUT_MS);
    http.addHeader("Content-Type", "application/json");
    int codigo = http.POST(json);
    String corpo = codigo > 0 ? http.getString() : String("");
    http.end();

    if (codigo == 201) {
      JsonDocument resposta;
      deserializeJson(resposta, corpo);
      Serial.println("Enviado: " + json);
      Serial.printf("API 201 | status_final=%s | %s\r\n",
                    resposta["status_final"] | "?", resposta["recomendacao"] | "");
      return true;
    }
    if (codigo > 0) {
      Serial.printf("API recusou (%d): %s\r\n", codigo, corpo.c_str());
      return false;
    }
    Serial.println("API offline: " + json);
    return false;
  }
}
