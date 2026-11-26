# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/seguranca/assinatura.py
# Resumo:  Assinatura HMAC-SHA256 das leituras do totem e verificação de horário e
#          nonce para bloquear leituras forjadas, alteradas ou reenviadas (replay).
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import hashlib
import hmac
import threading
import time

JANELA_SEGUNDOS = 120


def mensagem(timestamp: str, nonce: str, corpo: bytes) -> bytes:
    return timestamp.encode() + b"\n" + nonce.encode() + b"\n" + corpo


def assinar(segredo_hex: str, timestamp: str, nonce: str, corpo: bytes) -> str:
    """HMAC-SHA256 do corpo exato + horário + número único. Quem não tem o segredo não consegue assinar."""
    return hmac.new(bytes.fromhex(segredo_hex), mensagem(timestamp, nonce, corpo), hashlib.sha256).hexdigest()


class Verificador:
    """Confere assinatura, horário e reuso de nonce (anti-replay)."""

    def __init__(self, janela=JANELA_SEGUNDOS):
        self.janela = janela
        self.vistos = {}
        self.trava = threading.Lock()

    def verificar(self, segredo_hex, timestamp, nonce, assinatura, corpo, agora=None):
        agora = time.time() if agora is None else agora
        if not (timestamp and nonce and assinatura):
            return "cabecalho_ausente"
        if not timestamp.isdigit() or abs(agora - int(timestamp)) > self.janela:
            return "horario_fora_da_janela"
        if not (8 <= len(nonce) <= 64 and nonce.isalnum()):
            return "nonce_invalido"
        esperado = assinar(segredo_hex, timestamp, nonce, corpo)
        if not hmac.compare_digest(esperado, assinatura.lower()):
            return "assinatura_invalida"
        with self.trava:
            self.vistos = {n: t for n, t in self.vistos.items() if agora - t <= self.janela}
            if nonce in self.vistos:
                return "replay"
            self.vistos[nonce] = agora
        return None
