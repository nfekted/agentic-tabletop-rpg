# Ações equivalentes às opções do menu do main.py original:
# iniciar/finalizar rodada, falar com todos, falar direcionado,
# aprovação de respostas e redirecionamento de dúvidas.
import streamlit as st

from config import carregar_agentes
from fichas import obter_status_jogador
from memoria import GerenciadorMemoriaRPG
from agentes import gerar_resposta_agente
from tags import (
    extrair_tags_resposta,
    formatar_conteudo_publico,
    tem_acao,
    tem_duvida,
    apenas_pensamento,
)

from ui.fala import registrar_fala, limpar_fala


def salvar_pensamento_privado(agente: str, resposta: str):
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(
            f"{agente} (pensamento): {resposta}", [agente]
        )
    st.session_state.envolvidos_rodada_atual.add(agente)
    registrar_fala(agente, resposta, aprovada=True, privado=True)


def acao_iniciar_rodada():
    st.session_state.rodada_ativa = True
    st.session_state.envolvidos_rodada_atual = set()
    GerenciadorMemoriaRPG.salvar_log_rodada_atual(
        "--- ÍNICIO DA RODADA ---", carregar_agentes()
    )
    st.session_state.mensagem_info = "🟢 Rodada iniciada."


def acao_cancelar_rodada(motivo: str):
    if not st.session_state.rodada_ativa:
        st.session_state.mensagem_info = "⚠️ Nenhuma rodada ativa para cancelar."
        return

    # Mover arquivos temporários e incluir log/motivo
    GerenciadorMemoriaRPG.cancelar_rodada(motivo)

    # Reverter estados para "sem rodada ativa" e limpar pendências
    st.session_state.rodada_ativa = False
    st.session_state.envolvidos_rodada_atual = set()
    st.session_state.historico = []
    st.session_state.ultima_fala = {}
    st.session_state.pending_principal = None
    st.session_state.pending_redirects = []
    st.session_state.aguardando_redirect = None

    st.session_state.mensagem_info = (
        f"🚫 Rodada cancelada com sucesso. Motivo: {motivo}"
    )


def acao_finalizar_rodada():
    if not st.session_state.rodada_ativa:
        st.session_state.mensagem_info = "⚠️ Inicie a rodada antes de finalizar."
        return

    alvos = (
        list(st.session_state.envolvidos_rodada_atual)
        if st.session_state.envolvidos_rodada_atual
        else carregar_agentes()
    )
    GerenciadorMemoriaRPG.salvar_log_rodada_atual("--- FIM DA RODADA ---", alvos)
    GerenciadorMemoriaRPG.finalizar_rodada(alvos)

    nao_envolvidos = [ag for ag in carregar_agentes() if ag not in alvos]
    if nao_envolvidos:
        GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

    st.session_state.rodada_ativa = False
    st.session_state.historico = []
    st.session_state.ultima_fala = {}
    st.session_state.mensagem_info = "⏹️ Rodada finalizada e memória consolidada."


def acao_falar_com_todos(presentes, comando_mestre, caminho_imagem):
    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
    st.session_state.historico.append(log_mestre)
    for p in presentes:
        st.session_state.envolvidos_rodada_atual.add(p)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, presentes)

    for ag in presentes:
        if obter_status_jogador(ag) != "vivo":
            continue
        resposta = gerar_resposta_agente(
            ag,
            f"O mestre disse a todos: '{comando_mestre}'. Dê sua reação no formato com tags [pensamento], [fala], [acao] ou [duvida].",
            st.session_state.historico,
            caminho_imagem=caminho_imagem,
        )
        tags = extrair_tags_resposta(resposta)
        publico = formatar_conteudo_publico(tags)

        # 1. Salva pensamento na memória privada do personagem
        if tags.get("pensamento"):
            salvar_pensamento_privado(
                ag, f"[pensamento]{tags['pensamento']}[/pensamento]"
            )

        # 2. Se houver fala ou ação pública, espelha para o chat e para os presentes
        if publico:
            log_ag = f"{ag}: {publico}"
            st.session_state.historico.append(log_ag)
            registrar_fala(ag, publico, aprovada=True, privado=False)
            if st.session_state.rodada_ativa:
                GerenciadorMemoriaRPG.salvar_resposta_agente(ag, resposta, presentes)
        elif not tags.get("pensamento"):
            log_ag = f"{ag}: {resposta}"
            st.session_state.historico.append(log_ag)
            registrar_fala(ag, resposta, aprovada=True, privado=False)
            if st.session_state.rodada_ativa:
                GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_ag, presentes)


def acao_falar_direcionado(presentes, is_privado, comando_mestre, caminho_imagem):
    agentes_alvo_log = presentes if is_privado else carregar_agentes()
    for p in agentes_alvo_log:
        st.session_state.envolvidos_rodada_atual.add(p)

    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
    st.session_state.historico.append(log_mestre)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)

    alvo_principal = presentes[0]
    status_alvo = obter_status_jogador(alvo_principal)
    if status_alvo != "vivo":
        st.session_state.mensagem_info = f"⚠️ Não é possível falar com {alvo_principal}. Status: [{status_alvo.upper()}]."
        return

    resposta = gerar_resposta_agente(
        alvo_principal,
        f"O mestre direcionou a você: '{comando_mestre}'. Responda usando as tags [pensamento], [fala], [acao] ou [duvida].",
        st.session_state.historico,
        caminho_imagem=caminho_imagem,
    )

    tags = extrair_tags_resposta(resposta)
    publico = formatar_conteudo_publico(tags)

    # 1. Se houver pensamento, grava imediatamente na memória privada do personagem
    if tags.get("pensamento"):
        salvar_pensamento_privado(
            alvo_principal, f"[pensamento]{tags['pensamento']}[/pensamento]"
        )

    # 2. Se for apenas pensamento, encerra o turno
    if apenas_pensamento(tags):
        st.session_state.mensagem_info = f"💭 {alvo_principal} teve um pensamento privado — não realizou ações públicas neste turno."
        return

    # 3. Se houver conteúdo público (fala/ação/dúvida), envia para aprovação do Mestre
    conteudo_para_aprovar = publico or resposta
    st.session_state.pending_principal = {
        "alvo": alvo_principal,
        "resposta_completa": resposta,
        "conteudo_publico": conteudo_para_aprovar,
        "tags": tags,
        "presentes": presentes,
        "agentes_alvo_log": agentes_alvo_log,
    }
    registrar_fala(alvo_principal, conteudo_para_aprovar, aprovada=False, privado=False)


def aprovar_principal():
    p = st.session_state.pending_principal
    tags = p.get("tags") or extrair_tags_resposta(p["resposta_completa"])
    publico = p["conteudo_publico"]

    log_acao = f"{p['alvo']}: {publico}"
    st.session_state.historico.append(log_acao)
    registrar_fala(p["alvo"], publico, aprovada=True, privado=False)

    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            p["alvo"], p["resposta_completa"], p["agentes_alvo_log"]
        )

    outros_presentes = [x for x in p["presentes"] if x != p["alvo"]]

    if tem_duvida(tags) and outros_presentes:
        candidatos = [x for x in outros_presentes if obter_status_jogador(x) == "vivo"]
        st.session_state.aguardando_redirect = {
            "candidatos": candidatos,
            "alvo_principal": p["alvo"],
            "resposta_pergunta": tags.get("duvida") or publico,
            "agentes_alvo_log": p["agentes_alvo_log"],
        }
    elif tem_acao(tags):
        st.session_state.mensagem_info = (
            f"✅ Ação de {p['alvo']} resolvida. Nenhuma reação automática dos demais."
        )
    elif outros_presentes:
        for ou in outros_presentes:
            if obter_status_jogador(ou) != "vivo":
                continue
            resp_outro = gerar_resposta_agente(
                ou,
                f"O jogador {p['alvo']} acabou de dizer/fazer: '{publico}'. Você concorda, opina, faz ressalva "
                f"ou apenas pensa a respeito? Use as tags [pensamento], [fala], [acao] ou [duvida]. Seja breve.",
                st.session_state.historico,
                caminho_imagem=None,
            )
            tags_outro = extrair_tags_resposta(resp_outro)
            publico_outro = formatar_conteudo_publico(tags_outro)

            if tags_outro.get("pensamento"):
                salvar_pensamento_privado(
                    ou, f"[pensamento]{tags_outro['pensamento']}[/pensamento]"
                )

            if publico_outro:
                log_outro = f"{ou} (opinião): {publico_outro}"
                st.session_state.historico.append(log_outro)
                registrar_fala(ou, publico_outro, aprovada=True, privado=False)
                if st.session_state.rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(
                        ou, resp_outro, p["agentes_alvo_log"]
                    )

    st.session_state.pending_principal = None


def gerar_redirects(destinos):
    ar = st.session_state.aguardando_redirect
    pendentes = []
    for destino in destinos:
        resp = gerar_resposta_agente(
            destino,
            f"{ar['alvo_principal']} perguntou diretamente a você: '{ar['resposta_pergunta']}'. "
            f"Responda diretamente usando as tags [pensamento], [fala], [acao] ou [duvida].",
            st.session_state.historico,
            caminho_imagem=None,
        )
        tags = extrair_tags_resposta(resp)
        publico = formatar_conteudo_publico(tags)

        if tags.get("pensamento"):
            salvar_pensamento_privado(
                destino, f"[pensamento]{tags['pensamento']}[/pensamento]"
            )

        if apenas_pensamento(tags):
            continue

        conteudo_para_aprovar = publico or resp
        pendentes.append(
            {
                "destino": destino,
                "resposta_completa": resp,
                "conteudo_publico": conteudo_para_aprovar,
                "tags": tags,
                "alvo_principal": ar["alvo_principal"],
                "agentes_alvo_log": ar["agentes_alvo_log"],
            }
        )
        registrar_fala(destino, conteudo_para_aprovar, aprovada=False, privado=False)

    st.session_state.pending_redirects = pendentes
    st.session_state.aguardando_redirect = None
    if not pendentes and destinos:
        st.session_state.mensagem_info = "💭 A resposta foi um pensamento privado — não há nada para aprovar/espelhar."


def aprovar_redirect(indice):
    r = st.session_state.pending_redirects.pop(indice)
    log_redirect = (
        f"{r['destino']} (resposta a {r['alvo_principal']}): {r['conteudo_publico']}"
    )
    st.session_state.historico.append(log_redirect)
    registrar_fala(r["destino"], r["conteudo_publico"], aprovada=True, privado=False)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            r["destino"], r["resposta_completa"], r["agentes_alvo_log"]
        )


def descartar_redirect(indice):
    r = st.session_state.pending_redirects.pop(indice)
    limpar_fala(r["destino"])
