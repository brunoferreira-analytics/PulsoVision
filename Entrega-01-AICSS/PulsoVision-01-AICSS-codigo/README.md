# 01 · AI Computer Systems & Sensors — Totem de Lotação

O totem ESP32 fica na recepção da UBS. O ultrassônico (HC-SR04) mede o tamanho da fila e o PIR mede se ela anda.
A cada 3 s ele decide **OK / ALERTA / LOTADO**, acende o LED e envia a leitura em JSON (contrato v1.0) para um servidor Python por socket TCP.

| Pasta / arquivo | O que é |
|---|---|
| `src/Regras.h` | Regras de decisão em C++ puro (as mesmas usadas pela API da disciplina 02) |
| `src/PulsoTotem.hpp`, `src/totem.ino` | Sensores, LEDs, Wi-Fi e laço principal do ESP32 |
| `test/teste_regras.cpp` | 21 testes automatizados das regras |
| `server_socket/servidor.py` | Recebe, valida e grava as leituras em `dados.csv` |
| `server_socket/simular_cenarios.py` | Envia leituras de teste (e inválidas, com `--invalidos`) |
| `evidencias/` | Prints dos cenários T1 a T7 e o `dados.csv` real do totem |

## Como rodar
```bash
g++ -std=c++17 -Isrc test/teste_regras.cpp -o teste && ./teste   # 21 testes das regras
python server_socket/servidor.py                                  # servidor na porta 5000
# no VS Code: PlatformIO Build e depois Wokwi: Start Simulator (diagram.json + wokwi.toml)
```
