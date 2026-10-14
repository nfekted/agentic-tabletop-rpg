# Ações do mestre: rodada, falas e aprovação de chamadas (estado em services.sessao)
import random
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
    # texto do balão (só o mestre vê): o pensamento vem antes da parte pública
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


def _exigir_rodada():
    if not obter()["rodada_ativa"]:
        raise ErroNegocio("Inicie a rodada antes de falar com os jogadores.")


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


def preparar_finalizar() -> list[str]:
    # Marca o fim da rodada na memória de cada alvo; o historiador (um personagem por vez) roda na fila.
    s = obter()
    if not s["rodada_ativa"]:
        raise ErroNegocio("Inicie a rodada antes de finalizar.")

    alvos = list(s["envolvidos"]) if s["envolvidos"] else carregar_agentes()
    GerenciadorMemoriaRPG.salvar_log_rodada_atual("--- FIM DA RODADA ---", alvos)
    return alvos


def fechar_rodada(alvos: list[str]) -> str:
    s = obter()
    todos = carregar_agentes()
    nao_envolvidos = [ag for ag in todos if ag not in alvos]
    if nao_envolvidos:
        GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

    s["rodada_ativa"] = False
    s["envolvidos"] = []
    s["historico"] = []
    # ultima_fala fica: é só referência visual dos balões (não entra em nenhum prompt) e cada nova fala a substitui
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
    # aplica na hora; só o efeito de chamar outro jogador espera a aprovação do mestre
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
            "chamar_texto": tags["chamar"],
            "presentes": list(presentes),
        })
    salvar()
    if apenas_pensamento(tags):
        return f"💭 {agente} teve um pensamento privado — não realizou ações públicas neste turno."
    return None


def preparar_falar_todos(comando: str) -> tuple[list[str], list[dict]]:
    # Registra a fala do mestre; devolve (presentes, itens da fila: um por jogador).
    _exigir_rodada()
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

    instrucao = f"O mestre disse a todos: '{comando}'. Dê sua reação no formato com tags {_TAGS}."
    # a ordem de resposta é sorteada a cada mensagem geral: quem responde primeiro influencia os demais
    ordem = random.sample(presentes, len(presentes))
    return presentes, [{"agente": ag, "instrucao": instrucao} for ag in ordem]


def preparar_falar_direcionado(presentes: list[str], is_privado: bool, comando: str) -> tuple[list[str], list[dict]]:
    # pública: todos ouvem e só os alvos respondem, na ordem; privada: só os selecionados ouvem e respondem
    _exigir_rodada()
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

    instrucao = f"O mestre direcionou a você: '{comando}'. Responda usando as tags {_TAGS}."
    return agentes_alvo_log, [{"agente": alvo, "instrucao": instrucao} for alvo in presentes]


def _tirar_chamada(chamada_id: str) -> dict:
    s = obter()
    for i, c in enumerate(s["pending_chamadas"]):
        if c["id"] == chamada_id:
            return s["pending_chamadas"].pop(i)
    raise ErroNegocio("Chamada pendente não encontrada.")


def preparar_aprovar_chamada(chamada_id: str) -> tuple[list[str], list[dict], str]:
    # Aciona o jogador chamado: entra na cena (se ainda não estava); devolve (presentes, itens, rótulo).
    _exigir_rodada()
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

    instrucao = f"{origem} chamou você: '{c['mensagem']}'. Responda usando as tags {_TAGS}."
    return presentes, [{"agente": destino, "instrucao": instrucao}], f"chamado por {origem}"


def responder(agente: str, instrucao: str, presentes: list[str], rotulo: str = "", caminho_imagem=None) -> str | None:
    # Um passo da fila: o agente responde e a resposta entra na história e na memória.
    resposta = _gerar(agente, instrucao, caminho_imagem)
    return _processar_resposta(agente, resposta, presentes, rotulo)


def descartar_chamada(chamada_id: str):
    # Recusa: o chamado não aciona ninguém e vira fala comum ([chamar] -> [fala]), mantendo o que foi dito
    # na história e na memória da rodada.
    s = obter()
    c = _tirar_chamada(chamada_id)
    texto = c.get("chamar_texto")
    if texto:
        trecho, novo = f"[chamar]{texto}[/chamar]", f"[fala]{texto}[/fala]"
        for i in range(len(s["historico"]) - 1, -1, -1):
            if trecho in s["historico"][i]:
                s["historico"][i] = s["historico"][i].replace(trecho, novo)
                break
        fala = s["ultima_fala"].get(c["origem"])
        if fala and trecho in fala["texto"]:
            fala["texto"] = fala["texto"].replace(trecho, novo)
        if s["rodada_ativa"]:
            GerenciadorMemoriaRPG.substituir_trecho_temp(trecho, novo, c["presentes"])
    salvar()
