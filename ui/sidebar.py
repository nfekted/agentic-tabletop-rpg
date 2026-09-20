# Barra lateral: configurações da LLM, controle de rodada,
# troca rápida de conjunto de regras e cadastro de novos jogadores.
import streamlit as st

from config import (
    adicionar_agente,
    carregar_configuracao,
    salvar_configuracao,
    PROVEDORES,
)
from fichas import listar_arquivos_regras, obter_regra_ativa, definir_regra_ativa
from memoria import obter_pasta_agente

from ui.estado import indice_seguro
from ui.acoes import acao_cancelar_rodada, acao_iniciar_rodada, acao_finalizar_rodada


@st.dialog("Confirmar Cancelamento da Rodada")
def modal_confirmar_cancelamento():
    st.write(
        "Tem certeza que deseja cancelar a rodada atual? As alterações temporárias serão desfeitas."
    )
    motivo = st.text_input(
        "Motivo do cancelamento:",
        placeholder="Ex: Erro nas ações dos jogadores / Interrupção da mesa",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Confirmar Cancelamento", type="primary", use_container_width=True
        ):
            if not motivo.strip():
                st.error("Por favor, informe um motivo.")
            else:
                acao_cancelar_rodada(motivo.strip())
                st.rerun()
    with col2:
        if st.button("Voltar", use_container_width=True):
            st.rerun()


def renderizar_sidebar():
    with st.sidebar:
        # Menu suspenso/retrátil para as configurações de LLM
        with st.expander("⚙️ Configurações da LLM", expanded=False):
            cfg = carregar_configuracao()

            provedor_atual = cfg.get("provedor", PROVEDORES[0])
            index_padrao = (
                PROVEDORES.index(provedor_atual) if provedor_atual in PROVEDORES else 0
            )

            provedor_sel = st.selectbox("Provedor LLM", PROVEDORES, index=index_padrao)

            if provedor_sel in ["Gemini 3.5-flash", "GPT-luna"]:
                key_input = st.text_input(
                    "API Key", value=cfg.get("api_key", ""), type="password"
                )
                url_input = cfg.get("base_url", "")
            else:
                key_input = cfg.get("api_key", "")
                url_input = st.text_input(
                    "Endereço (Host/URL)",
                    value=cfg.get("base_url", "http://localhost:8000/v1"),
                )

            if st.button("💾 Salvar Configurações", use_container_width=True):
                salvar_configuracao(
                    {
                        "provedor": provedor_sel,
                        "api_key": key_input,
                        "base_url": url_input,
                    }
                )
                st.session_state.mensagem_info = (
                    "✅ Configurações de LLM salvas com sucesso!"
                )
                st.rerun()

        with st.expander("➕ Adicionar Jogador", expanded=False):
            with st.form("form_novo_jogador", clear_on_submit=True):
                novo_nome = st.text_input("Nome (sem espaços, ex: JogadorD)")
                enviado = st.form_submit_button("Adicionar")
                if enviado:
                    if adicionar_agente(novo_nome):
                        obter_pasta_agente(novo_nome.strip())
                        st.session_state.mensagem_info = (
                            f"✅ {novo_nome.strip()} adicionado à mesa."
                        )
                    else:
                        st.session_state.mensagem_info = (
                            "⚠️ Nome inválido ou já existente."
                        )
                    st.rerun()

            st.caption(
                "Novos jogadores entram automaticamente na fila de cards abaixo — "
                "não é preciso reiniciar o app."
            )

        st.divider()

        st.header("⚙️ Mesa")

        if st.session_state.rodada_ativa:
            st.success("Rodada em andamento")
            col_fim, col_canc = st.columns(2)
            with col_fim:
                if st.button("⏹️ Finalizar", use_container_width=True):
                    acao_finalizar_rodada()
                    st.rerun()
            with col_canc:
                if st.button("🚫 Cancelar", use_container_width=True):
                    modal_confirmar_cancelamento()
        else:
            st.info("Nenhuma rodada ativa")
            if st.button("▶️ Iniciar Rodada", use_container_width=True):
                acao_iniciar_rodada()
                st.rerun()

        st.divider()

        arquivos_regras_sidebar = listar_arquivos_regras()
        regra_ativa_sidebar = obter_regra_ativa()
        st.caption("📖 Regras em uso agora")
        troca_rapida = st.selectbox(
            "Trocar rapidamente",
            arquivos_regras_sidebar,
            index=indice_seguro(arquivos_regras_sidebar, regra_ativa_sidebar),
            key="troca_rapida_regras",
            label_visibility="collapsed",
        )
        if troca_rapida != regra_ativa_sidebar:
            definir_regra_ativa(troca_rapida)
            st.session_state.mensagem_info = (
                f"⭐ '{troca_rapida}' passou a ser o conjunto ativo."
            )
            st.rerun()

        if st.button(
            "✏️ Gerenciar / Criar Regras (arquivos/regras/)",
            use_container_width=True,
        ):
            st.session_state.editando_regras = True
            st.session_state.editando_ficha = None
            st.session_state.vendo_memoria = None
            st.session_state.trocando_avatar = None
            st.rerun()

        st.divider()
