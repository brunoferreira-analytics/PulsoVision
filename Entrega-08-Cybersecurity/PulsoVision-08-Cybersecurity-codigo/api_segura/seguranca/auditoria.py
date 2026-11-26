# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/seguranca/auditoria.py
# Resumo:  Log de auditoria em JSON Lines com cadeia de hashes SHA-256: editar ou
#          apagar uma linha é detectado na verificação.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path

INICIO_CADEIA = "0" * 64


class Auditoria:
    """Log de eventos em JSON Lines. Cada linha guarda o hash da anterior: apagar ou editar uma linha quebra a cadeia."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.trava = threading.Lock()

    def _ultimo_hash(self):
        if not self.caminho.exists():
            return INICIO_CADEIA
        ultima = None
        with self.caminho.open(encoding="utf-8") as arquivo:
            for linha in arquivo:
                if linha.strip():
                    ultima = linha
        return json.loads(ultima)["hash"] if ultima else INICIO_CADEIA

    def registrar(self, evento, **campos):
        with self.trava:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            registro = {"data_hora": datetime.now().isoformat(timespec="seconds"), "evento": evento, **campos,
                        "hash_anterior": self._ultimo_hash()}
            registro["hash"] = hashlib.sha256(json.dumps(registro, sort_keys=True, ensure_ascii=False)
                                              .encode("utf-8")).hexdigest()
            with self.caminho.open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def listar(self, limite=100):
        if not self.caminho.exists():
            return []
        with self.caminho.open(encoding="utf-8") as arquivo:
            linhas = [json.loads(l) for l in arquivo if l.strip()]
        return linhas[-limite:]

    def verificar(self):
        """Devolve (True, None) se a cadeia está íntegra, ou (False, número da primeira linha adulterada)."""
        anterior = INICIO_CADEIA
        if not self.caminho.exists():
            return True, None
        with self.caminho.open(encoding="utf-8") as arquivo:
            for numero, linha in enumerate(arquivo, start=1):
                if not linha.strip():
                    continue
                registro = json.loads(linha)
                guardado = registro.pop("hash")
                calculado = hashlib.sha256(json.dumps(registro, sort_keys=True, ensure_ascii=False)
                                           .encode("utf-8")).hexdigest()
                if registro["hash_anterior"] != anterior or calculado != guardado:
                    return False, numero
                anterior = guardado
        return True, None
