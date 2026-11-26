/*
 * PulsoVision · Totem de Lotação
 * Disciplina 02: Computational Thinking with Python · Global Solution 2026.2 — FIAP
 *
 * Arquivo: 02-python-api/totem-http/src/totem.ino
 * Resumo:  Programa principal do ESP32 (o mesmo totem do AICSS). A cada 3 s
 *          lê a fila e o movimento, decide o status, acende o LED e envia a
 *          leitura em JSON para a API REST por HTTP.
 *
 * Integrantes:
 *   - Tiago Thomaz Cesaro
 *   - Bruno Henrique Ferreira Ambrosio
 *   - Lucas Maximo dos Santos
 */

#include "PulsoTotem.hpp"

const unsigned long INTERVALO_COLETA_MS = 3000;
unsigned long ultimaColeta = 0;

Leitura leituraAtual = {0, 0.0, "CURTA", false, "FLUXO", 0, "OK", "FILA_CURTA"};
int idLeitura = 0;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("=== Pulso - Totem de Lotacao ===");
  Serial.print("Unidade: ");
  Serial.print(Unidade::NOME);
  Serial.print(" (CNES ");
  Serial.print(Unidade::CNES);
  Serial.println(")");

  Fila::iniciar();
  Movimento::iniciar();
  Sinalizacao::iniciar();
  Sinalizacao::atualizar();

  Conexao::conectar();

  Serial.println("id,fila_cm,fila_status,movimento,movimento_status,pessoas,status,motivo");
}

void loop() {
  Movimento::ler();

  if (millis() - ultimaColeta >= INTERVALO_COLETA_MS) {
    ultimaColeta = millis();
    idLeitura++;

    leituraAtual.id                = idLeitura;
    leituraAtual.filaDistanciaCm   = Fila::ler();
    leituraAtual.filaStatus        = Fila::avaliar(leituraAtual.filaDistanciaCm);
    leituraAtual.movimento         = Movimento::ler();
    leituraAtual.movimentoStatus   = Movimento::avaliar();
    leituraAtual.pessoasAguardando = Regras::estimarPessoas(leituraAtual.filaDistanciaCm);
    leituraAtual.status            = Regras::decidirStatus(leituraAtual.filaStatus,
                                                           Movimento::semFluxo(),
                                                           &leituraAtual.motivo);

    Sinalizacao::definir(leituraAtual.status);

    Serial.printf("%d,%.1f,%s,%d,%s,%d,%s,%s\r\n",
      leituraAtual.id,
      leituraAtual.filaDistanciaCm,
      leituraAtual.filaStatus,
      leituraAtual.movimento,
      leituraAtual.movimentoStatus,
      leituraAtual.pessoasAguardando,
      leituraAtual.status,
      leituraAtual.motivo
    );

    Envio::enviar(Envio::montarJson(leituraAtual));
  }

  Sinalizacao::atualizar();
  Conexao::manter();
}
