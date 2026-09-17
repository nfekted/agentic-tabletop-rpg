# Painel de visualização (somente leitura) da memória de um jogador.
import streamlit as st

from memoria import obter_arquivos_memoria


def renderizar_painel_memoria():
    if not st.session_state.vendo_memoria:
        return

    nome = st.session_state.vendo_memoria
    st.subheader(f"📜 Memória de {nome}")
    dados = obter_arquivos_memoria(nome)

    with st.expander("Rodada atual (em aberto)", expanded=True):
        st.text(dados["rodada_atual"] or "Nenhuma rodada em aberto para este jogador.")

    if dados["rodadas"]:
        with st.expander(f"Rodadas fechadas ({len(dados['rodadas'])})"):
            for nome_arq, conteudo in dados["rodadas"]:
                st.markdown(f"**{nome_arq}**")
                st.text(conteudo)
                st.markdown("---")

    if dados["cenas"]:
        with st.expander(f"Cenas compiladas ({len(dados['cenas'])})"):
            for nome_arq, conteudo in dados["cenas"]:
                st.markdown(f"**{nome_arq}**")
                st.text(conteudo)
                st.markdown("---")

    with st.expander("Histórico permanente (mesa.txt)"):
        st.text(dados["mesa"] or "Ainda não há capítulos compilados na mesa.txt.")

    if st.button("Fechar visualização", key=f"fechar_mem_{nome}"):
        st.session_state.vendo_memoria = None
        st.rerun()
    st.divider()
