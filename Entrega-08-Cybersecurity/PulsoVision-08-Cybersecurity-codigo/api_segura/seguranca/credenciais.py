# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/seguranca/credenciais.py
# Resumo:  Cofre de segredos: cadastro dos totens (fonte da verdade vinda do CNES),
#          segredo de cada totem, resumo SHA-256 dos tokens de perfil e pseudônimo
#          de IP para o log (LGPD).
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = PASTA / "segredos" / "segredos.json"

# Cadastro dos totens: a "fonte da verdade" de cada unidade vem do CNES, não do que o totem envia.
TOTENS_CADASTRADOS = {
    "TOTEM-4048296-01": {"cnes": "4048296", "nome_unidade": "UBS Jardim Paulista", "tipo_unidade": "UBS",
                         "cod_municipio": "351880"},
    "TOTEM-3179613-01": {"cnes": "3179613", "nome_unidade": "UBS Continental", "tipo_unidade": "UBS",
                         "cod_municipio": "351880"},
    "TOTEM-2062097-01": {"cnes": "2062097", "nome_unidade": "UBS Jardim Palmira", "tipo_unidade": "UBS",
                         "cod_municipio": "351880"},
}

PERFIS = ("gestor", "auditor")


def resumo_token(token: str) -> str:
    """Tokens têm 256 bits aleatórios: guardamos só o SHA-256, nunca o token em texto puro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def gerar(caminho: Path = CAMINHO_PADRAO) -> dict:
    """Cria segredos novos e devolve, uma única vez, os valores que precisam ser entregues a cada pessoa ou totem."""
    entregar = {"totens": {}, "tokens": {}}
    cofre = {"chave_pseudonimizacao": secrets.token_hex(32), "totens": {}, "perfis": {}}
    for id_totem, dados in TOTENS_CADASTRADOS.items():
        segredo = secrets.token_hex(32)
        cofre["totens"][id_totem] = {**dados, "segredo": segredo}
        entregar["totens"][id_totem] = segredo
    for perfil in PERFIS:
        token = secrets.token_urlsafe(32)
        cofre["perfis"][perfil] = [resumo_token(token)]
        entregar["tokens"][perfil] = token
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(cofre, indent=2), encoding="utf-8")
    try:
        os.chmod(caminho, 0o600)  # só o dono do processo lê o arquivo de segredos
    except OSError:
        pass
    return entregar


class Cofre:
    """Lê os segredos de um arquivo fora do código (caminho na variável PULSO_SEGREDOS)."""

    def __init__(self, caminho=None):
        caminho = Path(caminho or os.environ.get("PULSO_SEGREDOS", CAMINHO_PADRAO))
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de segredos não encontrado: {caminho}. Rode gerar_segredos.py.")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        self.chave_pseudonimizacao = bytes.fromhex(dados["chave_pseudonimizacao"])
        self.totens = dados["totens"]
        self.perfis = dados["perfis"]

    def totem(self, id_totem):
        return self.totens.get(id_totem)

    def perfil_do_token(self, token):
        if not token:
            return None
        resumo = resumo_token(token)
        for perfil, resumos in self.perfis.items():
            if any(hmac.compare_digest(resumo, r) for r in resumos):
                return perfil
        return None

    def pseudonimo(self, valor: str) -> str:
        """IP é dado pessoal (LGPD): o log guarda um apelido irreversível sem a chave, não o IP."""
        return hmac.new(self.chave_pseudonimizacao, valor.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
