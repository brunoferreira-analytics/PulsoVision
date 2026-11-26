# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/seguranca/limite.py
# Resumo:  Limite de taxa por janela deslizante (por IP e por totem), contra flood.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import threading
import time
from collections import defaultdict, deque


class LimiteTaxa:
    """Janela deslizante: no máximo `maximo` pedidos por `janela` segundos para cada chave (IP ou totem)."""

    def __init__(self, maximo, janela=60):
        self.maximo = maximo
        self.janela = janela
        self.pedidos = defaultdict(deque)
        self.trava = threading.Lock()

    def permitir(self, chave, agora=None):
        agora = time.monotonic() if agora is None else agora
        with self.trava:
            fila = self.pedidos[chave]
            while fila and agora - fila[0] > self.janela:
                fila.popleft()
            if len(fila) >= self.maximo:
                return False
            fila.append(agora)
            return True
