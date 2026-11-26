# PulsoVision · Segurança da Solução
# Disciplina 08: Cognitive Cybersecurity · Global Solution 2026.2 — FIAP
#
# Arquivo: 08-cybersecurity/api_segura/app_segura.py
# Resumo:  API segura: a mesma API de lotação da disciplina 02 com uma camada de
#          segurança. Exige leitura assinada (HMAC) de totem cadastrado, bloqueia
#          replay, vincula totem à unidade, limita requisições, controla acesso por
#          perfil, grava log de auditoria e envia cabeçalhos de segurança.
#
# Integrantes:
#   - Tiago Thomaz Cesaro
#   - Bruno Henrique Ferreira Ambrosio
#   - Lucas Maximo dos Santos

import sys
from functools import wraps
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "api_original"))  # reaproveita a API da disciplina 02, sem copiar regra de negócio

from main import create_app as criar_api_original  # noqa: E402
from models.leitura import validar  # noqa: E402
from routes.leituras import get_repositorio, ler_leitura  # noqa: E402
from services.leituras import processar  # noqa: E402

from seguranca.assinatura import Verificador  # noqa: E402
from seguranca.auditoria import Auditoria  # noqa: E402
from seguranca.credenciais import Cofre  # noqa: E402
from seguranca.limite import LimiteTaxa  # noqa: E402
from seguranca.sanitizar import neutralizar_registro  # noqa: E402

CABECALHOS_SEGURANCA = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}


def origem():
    return current_app.extensions["cofre"].pseudonimo(request.remote_addr or "desconhecido")


def auditar(evento, status, **campos):
    current_app.extensions["auditoria"].registrar(
        evento, metodo=request.method, rota=request.path, status=status, origem=origem(), **campos)


def negar(status, evento, mensagem, **campos):
    auditar(evento, status, **campos)
    resposta = jsonify({"erro": mensagem})
    resposta.status_code = status
    return resposta


def requer_perfil(*permitidos):
    """Controle de acesso: o token Bearer precisa pertencer a um perfil autorizado para a rota."""
    def decorador(funcao):
        @wraps(funcao)
        def protegida(*args, **kwargs):
            cabecalho = request.headers.get("Authorization", "")
            token = cabecalho[7:] if cabecalho.startswith("Bearer ") else None
            perfil = current_app.extensions["cofre"].perfil_do_token(token)
            if perfil is None:
                return negar(401, "acesso_sem_credencial", "Credencial ausente ou inválida.")
            if perfil not in permitidos:
                return negar(403, "acesso_negado_perfil", "Seu perfil não tem acesso a esta rota.", perfil=perfil)
            g.perfil = perfil
            return funcao(*args, **kwargs)
        return protegida
    return decorador


def receber_leitura_segura():
    """POST /leituras: só aceita leitura assinada por um totem cadastrado, para a própria unidade."""
    ext = current_app.extensions
    id_totem = request.headers.get("X-Totem-Id", "")
    cadastro = ext["cofre"].totem(id_totem)
    if cadastro is None:
        return negar(401, "totem_desconhecido", "Totem não autenticado.")

    falha = ext["verificador"].verificar(
        cadastro["segredo"], request.headers.get("X-Timestamp"), request.headers.get("X-Nonce"),
        request.headers.get("X-Assinatura"), request.get_data(cache=True))
    if falha == "replay":
        return negar(409, "replay_bloqueado", "Leitura repetida recusada.", totem=id_totem)
    if falha:
        return negar(401, falha, "Totem não autenticado.", totem=id_totem)
    if not ext["limite_totem"].permitir(id_totem):
        return negar(429, "limite_totem_excedido", "Muitas leituras em pouco tempo.", totem=id_totem)

    leitura = ler_leitura()
    erros = validar(leitura)
    if erros:
        auditar("leitura_fora_do_contrato", 400, totem=id_totem, detalhe=erros[:5])
        return jsonify({"erro": "Leitura fora do contrato v1.0.", "detalhes": erros}), 400
    if leitura["id_totem"] != id_totem or leitura["cnes"] != cadastro["cnes"]:
        return negar(403, "unidade_divergente", "O totem só pode informar a própria unidade.", totem=id_totem)

    # Nome, tipo e município vêm do cadastro (CNES), nunca do texto enviado pelo dispositivo.
    for campo in ("nome_unidade", "tipo_unidade", "cod_municipio"):
        leitura[campo] = cadastro[campo]
    registro = neutralizar_registro(processar(leitura))
    get_repositorio().salvar(registro)
    auditar("leitura_aceita", 201, totem=id_totem, id_leitura=leitura["id_leitura"],
            status_final=registro["status_final"])
    return jsonify(registro), 201


auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditoria")


@auditoria_bp.get("")
@requer_perfil("auditor")
def ver_auditoria():
    ext = current_app.extensions["auditoria"]
    integra, linha = ext.verificar()
    return jsonify({"cadeia_integra": integra, "primeira_linha_adulterada": linha, "eventos": ext.listar(50)})


def create_app_segura(config=None):
    app = criar_api_original({"CSV_LEITURAS": PASTA / "dados" / "leituras.csv", **(config or {})})
    app.config.setdefault("LOG_AUDITORIA", PASTA / "logs" / "auditoria.jsonl")
    app.extensions["cofre"] = Cofre(app.config.get("SEGREDOS"))
    app.extensions["auditoria"] = Auditoria(app.config["LOG_AUDITORIA"])
    app.extensions["verificador"] = Verificador()
    app.extensions["limite_totem"] = LimiteTaxa(app.config.get("LIMITE_TOTEM_POR_MINUTO", 20))
    app.extensions["limite_ip"] = LimiteTaxa(app.config.get("LIMITE_IP_POR_MINUTO", 60))

    # Substitui as rotas originais pelas versões protegidas (mesma regra de negócio da disciplina 02).
    app.view_functions["leituras.receber_leitura"] = receber_leitura_segura
    app.view_functions["leituras.listar_leituras"] = requer_perfil("gestor", "auditor")(
        app.view_functions["leituras.listar_leituras"])
    app.register_blueprint(auditoria_bp)

    @app.before_request
    def limitar_por_ip():
        if not current_app.extensions["limite_ip"].permitir(origem()):
            return negar(429, "limite_ip_excedido", "Muitas requisições. Tente de novo em instantes.")
        return None

    @app.after_request
    def cabecalhos(resposta):
        resposta.headers.update(CABECALHOS_SEGURANCA)
        if request.is_secure:
            resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resposta

    return app
