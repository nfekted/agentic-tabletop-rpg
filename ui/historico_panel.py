# Painel de histórico da cena/rodada atual (chat da mesa).
import streamlit as st


def renderizar_historico():
    st.subheader("🗒️ Histórico da cena atual")
    if not st.session_state.historico:
        st.caption("Nenhum evento ainda nesta rodada.")
        return

    for linha in st.session_state.historico:
        if ":" in linha:
            autor, resto = linha.split(":", 1)
        else:
            autor, resto = "Mestre", linha
        with st.chat_message(
            "assistant" if autor.strip() not in ("Mestre",) else "user"
        ):
            st.markdown(f"**{autor.strip()}**: {resto.strip()}")
