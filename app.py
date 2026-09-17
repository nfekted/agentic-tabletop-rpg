# Interface visual (Streamlit) para o Mestre conduzir a mesa de RPG
import streamlit as st

from config import carregar_agentes
from memoria import obter_pasta_agente

from ui.estado import inicializar_estado
from ui.sidebar import renderizar_sidebar
from ui.regras_panel import renderizar_painel_regras
from ui.jogadores import renderizar_titulo_e_cards
from ui.avatar_panel import renderizar_painel_avatar
from ui.ficha_panel import renderizar_painel_ficha
from ui.memoria_panel import renderizar_painel_memoria
from ui.acao_mestre_panel import renderizar_acao_mestre
from ui.pending_panel import renderizar_pending_panels
from ui.historico_panel import renderizar_historico

st.set_page_config(page_title="Mesa de RPG — Painel do Mestre", layout="wide")


# ----------------------------------------------------------------------------
# ESTADO DA SESSÃO
# ----------------------------------------------------------------------------
inicializar_estado()

for ag in carregar_agentes():
    obter_pasta_agente(ag)


# ----------------------------------------------------------------------------
# BARRA LATERAL
# ----------------------------------------------------------------------------
renderizar_sidebar()

if st.session_state.mensagem_info:
    st.info(st.session_state.mensagem_info)
    st.session_state.mensagem_info = None


# ----------------------------------------------------------------------------
# GERENCIAMENTO DE REGRAS
# ----------------------------------------------------------------------------
renderizar_painel_regras()


# ----------------------------------------------------------------------------
# TÍTULO E CARDS DE JOGADORES
# ----------------------------------------------------------------------------
agentes = carregar_agentes()
renderizar_titulo_e_cards(agentes)


# ----------------------------------------------------------------------------
# PAINÉIS CONDICIONAIS (foto / ficha / memória)
# ----------------------------------------------------------------------------
renderizar_painel_avatar()
renderizar_painel_ficha()
renderizar_painel_memoria()


# ----------------------------------------------------------------------------
# PAINEL DE AÇÃO DO MESTRE
# ----------------------------------------------------------------------------
renderizar_acao_mestre(agentes)


# ----------------------------------------------------------------------------
# CONFIRMAÇÕES (resposta principal / redirecionamento de dúvida / respostas redirecionadas)
# ----------------------------------------------------------------------------
renderizar_pending_panels()


# ----------------------------------------------------------------------------
# HISTÓRICO DA CENA/RODADA ATUAL
# ----------------------------------------------------------------------------
renderizar_historico()
