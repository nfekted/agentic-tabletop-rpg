# Ações do mestre (iniciar/cancelar/finalizar rodada, falar, aprovar ou não o acionamento de outro jogador).
# O estado da mesa vem de services.sessao; as rotas em api/routers/mestre.py só chamam estas funções.
import uuid

from rpg.config import carregar_agentes
from rpg.memoria import GerenciadorMemoriaRPG
from rpg.agentes import gerar_resposta_agente
from rpg.tags import (
    extrair_tags_resposta,
    formatar_conteudo_publico,
    apenas_pensamento,
    formatar_para_autor,
    separar_chamada,
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


def _fala_do_mestre(tags: dict, publico: str) -> str:
    # Texto do balão (só o mestre vê): o pensamento do personagem vem antes da parte pública.
    pensamento = tags.get("pensamento")
    return f"[pensamento]{pensamento}[/pensamento]\n{publico}" if pensamento else publico


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
    s["pending_chamadas"] = []


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


_TAGS = "[pensamento], [fala], [acao], [duvida] ou [chamar]"


def _preparar_resposta(agente: str, resposta: str):
    # Chamada inválida (nome desconhecido, o próprio autor ou sem mensagem) vira fala comum.
    tags = extrair_tags_resposta(resposta)
    chamada = None
    if tags.get("chamar"):
        nomes = [n for n in carregar_agentes() if n != agente]
        chamada = separar_chamada(tags["chamar"], nomes)
        if not chamada:
            tags["fala"] = " ".join(filter(None, [tags.get("fala"), tags["chamar"]]))
            tags["chamar"] = None
            resposta = formatar_para_autor(tags)
    return resposta, tags, chamada


def _processar_resposta(agente: str, resposta: str, presentes: list[str], rotulo: str = "") -> str | None:
    # Aplica a resposta na hora (histórico, balão e memória de quem presencia). Só o efeito de
    # chamar outro jogador fica pendente da aprovação do mestre.
    s = obter()
    resposta, tags, chamada = _preparar_resposta(agente, resposta)
    publico = formatar_conteudo_publico(tags)

    _pensamento_de(agente, tags)

    autor = f"{agente} ({rotulo})" if rotulo else agente
    if publico:
        s["historico"].append(f"{autor}: {publico}")
        registrar_fala(agente, _fala_do_mestre(tags, publico), aprovada=True, privado=False)
        if s["rodada_ativa"]:
            GerenciadorMemoriaRPG.salvar_resposta_agente(agente, resposta, presentes)
    elif not tags.get("pensamento"):
        log_ag = f"{autor}: {resposta}"
        s["historico"].append(log_ag)
        registrar_fala(agente, resposta, aprovada=True, privado=False)
        if s["rodada_ativa"]:
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_ag, presentes)

    if chamada:
        s["pending_chamadas"].append({
            "id": uuid.uuid4().hex[:8],
            "origem": agente,
            "destino": chamada[0],
            "mensagem": chamada[1],
            "conteudo_publico": publico,
            "presentes": list(presentes),
        })
    salvar()
    if apenas_pensamento(tags):
        return f"💭 {agente} teve um pensamento privado — não realizou ações públicas neste turno."
    return None


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
            f"O mestre disse a todos: '{comando}'. Dê sua reação no formato com tags {_TAGS}.",
            caminho_imagem,
        )
        _processar_resposta(ag, resposta, presentes)
    return None


def falar_direcionado(presentes: list[str], is_privado: bool, comando: str, caminho_imagem=None) -> str | None:
    # Pública: a mesa toda ouve (memória de todos) e só o alvo responde.
    # Privada: só os selecionados ouvem e todos eles respondem, em sequência.
    s = obter()
    if not presentes:
        raise ErroNegocio("Selecione ao menos um jogador.")
    if not is_privado and len(presentes) > 1:
        raise ErroNegocio("Selecione apenas um jogador (ou use Cena privada para um grupo).")

    agentes_alvo_log = presentes if is_privado else carregar_agentes()
    for p in agentes_alvo_log:
        _envolver(p)

    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando}"
    s["historico"].append(log_mestre)
    if s["rodada_ativa"]:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)
    salvar()

    mensagens = []
    for alvo in presentes:
        resposta = _gerar(
            alvo,
            f"O mestre direcionou a você: '{comando}'. Responda usando as tags {_TAGS}.",
            caminho_imagem,
        )
        msg = _processar_resposta(alvo, resposta, agentes_alvo_log)
        if msg:
            mensagens.append(msg)
    return "\n".join(mensagens) or None


def _tirar_chamada(chamada_id: str) -> dict:
    s = obter()
    for i, c in enumerate(s["pending_chamadas"]):
        if c["id"] == chamada_id:
            return s["pending_chamadas"].pop(i)
    raise ErroNegocio("Chamada pendente não encontrada.")


def aprovar_chamada(chamada_id: str) -> str | None:
    # Aciona o jogador chamado: entra na cena (se ainda não estava) e responde.
    s = obter()
    c = _tirar_chamada(chamada_id)
    origem, destino = c["origem"], c["destino"]
    presentes = list(c["presentes"])
    if destino not in presentes:
        presentes.append(destino)
        if s["rodada_ativa"] and c["conteudo_publico"]:
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(f"{origem}: {c['conteudo_publico']}", [destino])
    _envolver(destino)
    salvar()

    resposta = _gerar(
        destino,
        f"{origem} chamou você: '{c['mensagem']}'. Responda usando as tags {_TAGS}.",
    )
    return _processar_resposta(destino, resposta, presentes, f"chamado por {origem}")


def descartar_chamada(chamada_id: str) -> str:
    # Não aciona ninguém; a fala/ação de quem chamou continua registrada.
    c = _tirar_chamada(chamada_id)
    salvar()
    return f"Chamada não acionada: {c['destino']} não foi chamado. A fala de {c['origem']} continua registrada."
