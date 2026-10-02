# Ações do mestre (iniciar/cancelar/finalizar rodada, falar, aprovar, redirecionar dúvidas).
# O estado da mesa vem de services.sessao; as rotas em api/routers/mestre.py só chamam estas funções.
import uuid

from rpg.config import carregar_agentes
from rpg.memoria import GerenciadorMemoriaRPG
from rpg.agentes import gerar_resposta_agente
from rpg.tags import (
    extrair_tags_resposta,
    formatar_conteudo_publico,
    tem_acao,
    tem_duvida,
    apenas_pensamento,
)

from services import eventos
from services.sessao import (
    ErroNegocio,
    obter,
    salvar,
    registrar_fala,
    limpar_fala,
)


def _envolver(agente: str):
    s = obter()
    if agente not in s["envolvidos"]:
        s["envolvidos"].append(agente)


def _gerar(agente: str, instrucao: str, caminho_imagem=None) -> str:
    eventos.publicar("agente_respondendo", agente=agente)
    try:
        return gerar_resposta_agente(
            agente, instrucao, obter()["historico"], caminho_imagem=caminho_imagem
        )
    finally:
        eventos.publicar("agente_pronto", agente=agente)


def salvar_pensamento_privado(agente: str, resposta: str):
    s = obter()
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(
            f"{agente} (pensamento): {resposta}", [agente]
        )
    _envolver(agente)
    registrar_fala(agente, resposta, aprovada=True, privado=True)


def _pensamento_de(agente: str, tags: dict):
    if tags.get("pensamento"):
        salvar_pensamento_privado(agente, f"[pensamento]{tags['pensamento']}[/pensamento]")


def iniciar_rodada() -> str:
    s = obter()
    s["rodada_ativa"] = True
    s["envolvidos"] = []
    GerenciadorMemoriaRPG.salvar_log_rodada_atual(
        "--- ÍNICIO DA RODADA ---", carregar_agentes()
    )
    salvar()
    return "🟢 Rodada iniciada."


def _limpar_pendencias(s: dict):
    s["pending_principal"] = None
    s["pending_redirects"] = []
    s["aguardando_redirect"] = None


def cancelar_rodada(motivo: str) -> str:
    s = obter()
    if not s["rodada_ativa"]:
        raise ErroNegocio("Nenhuma rodada ativa para cancelar.")

    GerenciadorMemoriaRPG.cancelar_rodada(motivo)

    s["rodada_ativa"] = False
    s["envolvidos"] = []
    s["historico"] = []
    s["ultima_fala"] = {}
    _limpar_pendencias(s)
    salvar()
    return f"🚫 Rodada cancelada com sucesso. Motivo: {motivo}"


def finalizar_rodada() -> str:
    s = obter()
    if not s["rodada_ativa"]:
        raise ErroNegocio("Inicie a rodada antes de finalizar.")

    todos = carregar_agentes()
    alvos = list(s["envolvidos"]) if s["envolvidos"] else todos
    GerenciadorMemoriaRPG.salvar_log_rodada_atual("--- FIM DA RODADA ---", alvos)
    GerenciadorMemoriaRPG.finalizar_rodada(alvos)

    nao_envolvidos = [ag for ag in todos if ag not in alvos]
    if nao_envolvidos:
        GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

    s["rodada_ativa"] = False
    s["envolvidos"] = []
    s["historico"] = []
    s["ultima_fala"] = {}
    _limpar_pendencias(s)
    salvar()
    return "⏹️ Rodada finalizada e memória consolidada."


def falar_com_todos(comando: str, caminho_imagem=None) -> str | None:
    s = obter()
    presentes = carregar_agentes()
    if not presentes:
        raise ErroNegocio("Não há jogadores na mesa.")

    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando}"
    s["historico"].append(log_mestre)
    for p in presentes:
        _envolver(p)
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, presentes)
    salvar()

    for ag in presentes:
        resposta = _gerar(
            ag,
            f"O mestre disse a todos: '{comando}'. Dê sua reação no formato com tags [pensamento], [fala], [acao] ou [duvida].",
            caminho_imagem,
        )
        tags = extrair_tags_resposta(resposta)
        publico = formatar_conteudo_publico(tags)

        _pensamento_de(ag, tags)

        if publico:
            s["historico"].append(f"{ag}: {publico}")
            registrar_fala(ag, publico, aprovada=True, privado=False)
            if s["rodada_ativa"]:
                GerenciadorMemoriaRPG.salvar_resposta_agente(ag, resposta, presentes)
        elif not tags.get("pensamento"):
            log_ag = f"{ag}: {resposta}"
            s["historico"].append(log_ag)
            registrar_fala(ag, resposta, aprovada=True, privado=False)
            if s["rodada_ativa"]:
                GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_ag, presentes)
        salvar()
    return None


def falar_direcionado(presentes: list[str], is_privado: bool, comando: str, caminho_imagem=None) -> str | None:
    s = obter()
    if not presentes:
        raise ErroNegocio("Selecione ao menos um jogador.")

    agentes_alvo_log = presentes if is_privado else carregar_agentes()
    for p in agentes_alvo_log:
        _envolver(p)

    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando}"
    s["historico"].append(log_mestre)
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)
    salvar()

    alvo = presentes[0]
    resposta = _gerar(
        alvo,
        f"O mestre direcionou a você: '{comando}'. Responda usando as tags [pensamento], [fala], [acao] ou [duvida].",
        caminho_imagem,
    )
    tags = extrair_tags_resposta(resposta)
    publico = formatar_conteudo_publico(tags)

    _pensamento_de(alvo, tags)

    if apenas_pensamento(tags):
        salvar()
        return f"💭 {alvo} teve um pensamento privado — não realizou ações públicas neste turno."

    conteudo = publico or resposta
    s["pending_principal"] = {
        "alvo": alvo,
        "resposta_completa": resposta,
        "conteudo_publico": conteudo,
        "tags": tags,
        "presentes": presentes,
        "agentes_alvo_log": agentes_alvo_log,
    }
    registrar_fala(alvo, conteudo, aprovada=False, privado=False)
    salvar()
    return None


def aprovar_principal() -> str | None:
    s = obter()
    p = s["pending_principal"]
    if not p:
        raise ErroNegocio("Não há resposta pendente.")
    tags = p.get("tags") or extrair_tags_resposta(p["resposta_completa"])
    publico = p["conteudo_publico"]
    mensagem = None

    s["historico"].append(f"{p['alvo']}: {publico}")
    registrar_fala(p["alvo"], publico, aprovada=True, privado=False)
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            p["alvo"], p["resposta_completa"], p["agentes_alvo_log"]
        )

    outros = [x for x in p["presentes"] if x != p["alvo"]]
    # A pendência sai antes das chamadas longas: evita aprovar duas vezes.
    s["pending_principal"] = None
    salvar()

    if tem_duvida(tags) and outros:
        s["aguardando_redirect"] = {
            "candidatos": list(outros),
            "alvo_principal": p["alvo"],
            "resposta_pergunta": tags.get("duvida") or publico,
            "agentes_alvo_log": p["agentes_alvo_log"],
        }
    elif tem_acao(tags):
        mensagem = f"✅ Ação de {p['alvo']} resolvida. Nenhuma reação automática dos demais."
    elif outros:
        for ou in outros:
            resp_outro = _gerar(
                ou,
                f"O jogador {p['alvo']} acabou de dizer/fazer: '{publico}'. Você concorda, opina, faz ressalva "
                f"ou apenas pensa a respeito? Use as tags [pensamento], [fala], [acao] ou [duvida]. Seja breve.",
            )
            tags_outro = extrair_tags_resposta(resp_outro)
            publico_outro = formatar_conteudo_publico(tags_outro)

            _pensamento_de(ou, tags_outro)

            if publico_outro:
                s["historico"].append(f"{ou} (opinião): {publico_outro}")
                registrar_fala(ou, publico_outro, aprovada=True, privado=False)
                if s["rodada_ativa"]:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(
                        ou, resp_outro, p["agentes_alvo_log"]
                    )
            salvar()
    salvar()
    return mensagem


def descartar_principal() -> str:
    s = obter()
    p = s["pending_principal"]
    if not p:
        raise ErroNegocio("Não há resposta pendente.")
    limpar_fala(p["alvo"])
    s["pending_principal"] = None
    salvar()
    return "❌ Mensagem descartada. Nada foi salvo na história."


def ignorar_redirect():
    s = obter()
    s["aguardando_redirect"] = None
    salvar()


def gerar_redirects(destinos: list[str]) -> str | None:
    s = obter()
    ar = s["aguardando_redirect"]
    if not ar:
        raise ErroNegocio("Não há dúvida aguardando redirecionamento.")
    invalidos = [d for d in destinos if d not in ar["candidatos"]]
    if invalidos or not destinos:
        raise ErroNegocio("Destinos inválidos para esta dúvida.")

    pendentes = []
    for destino in destinos:
        resp = _gerar(
            destino,
            f"{ar['alvo_principal']} perguntou diretamente a você: '{ar['resposta_pergunta']}'. "
            f"Responda diretamente usando as tags [pensamento], [fala], [acao] ou [duvida].",
        )
        tags = extrair_tags_resposta(resp)
        publico = formatar_conteudo_publico(tags)

        _pensamento_de(destino, tags)

        if apenas_pensamento(tags):
            continue

        conteudo = publico or resp
        pendentes.append(
            {
                "id": uuid.uuid4().hex[:8],
                "destino": destino,
                "resposta_completa": resp,
                "conteudo_publico": conteudo,
                "tags": tags,
                "alvo_principal": ar["alvo_principal"],
                "agentes_alvo_log": ar["agentes_alvo_log"],
            }
        )
        registrar_fala(destino, conteudo, aprovada=False, privado=False)

    s["pending_redirects"] = pendentes
    s["aguardando_redirect"] = None
    salvar()
    if not pendentes:
        return "💭 A resposta foi um pensamento privado — não há nada para aprovar/espelhar."
    return None


def _tirar_redirect(redirect_id: str) -> dict:
    s = obter()
    for i, r in enumerate(s["pending_redirects"]):
        if r["id"] == redirect_id:
            return s["pending_redirects"].pop(i)
    raise ErroNegocio("Resposta pendente não encontrada.")


def aprovar_redirect(redirect_id: str):
    r = _tirar_redirect(redirect_id)
    s = obter()
    s["historico"].append(
        f"{r['destino']} (resposta a {r['alvo_principal']}): {r['conteudo_publico']}"
    )
    registrar_fala(r["destino"], r["conteudo_publico"], aprovada=True, privado=False)
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            r["destino"], r["resposta_completa"], r["agentes_alvo_log"]
        )
    salvar()


def descartar_redirect(redirect_id: str):
    r = _tirar_redirect(redirect_id)
    limpar_fala(r["destino"])
    salvar()
