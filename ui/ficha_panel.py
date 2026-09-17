# Painel de edição de ficha de um jogador.
import streamlit as st

from fichas import carregar_ficha, salvar_ficha


def renderizar_painel_ficha():
    if not st.session_state.editando_ficha:
        return

    nome = st.session_state.editando_ficha
    st.subheader(f"✏️ Editando ficha de {nome}")
    conteudo_ficha = st.text_area(
        "Conteúdo da ficha",
        value=carregar_ficha(nome),
        height=250,
        key=f"txt_ficha_{nome}",
    )
    c1, c2 = st.columns([1, 1])
    if c1.button("💾 Salvar ficha", type="primary", key=f"salvar_ficha_{nome}"):
        salvar_ficha(nome, conteudo_ficha)
        st.session_state.editando_ficha = None
        st.session_state.mensagem_info = f"✅ Ficha de {nome} salva."
        st.rerun()
    if c2.button("Cancelar", key=f"cancelar_ficha_{nome}"):
        st.session_state.editando_ficha = None
        st.rerun()
    st.divider()
