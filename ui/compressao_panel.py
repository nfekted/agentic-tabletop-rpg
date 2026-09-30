# Diálogo de roleplay que oferece comprimir a memória de um personagem quando o contexto passa do gatilho.
import streamlit as st

from memoria import GerenciadorMemoriaRPG
from metricas import calcular_contexto

# Abaixo disso, o peso do contexto não está na memória (é regras/ficha/histórico): comprimir não ajuda.
LIMITE_MEMORIA_UTIL_PCT = 15


@st.dialog("🧠 Mente sobrecarregada")
def modal_compressao_memoria(nome: str, memoria_util: bool):
    if not memoria_util:
        st.write(
            f"**{nome}** está com muitas coisas na cabeça, mas o peso não está nas lembranças: "
            "são as regras, a ficha e a conversa da rodada atual."
        )
        st.caption("Finalize a rodada ou reduza as regras/ficha para aliviar o contexto.")
        if st.button("Entendi", use_container_width=True, key=f"btn_entendi_{nome}"):
            st.rerun()
        return

    st.write(
        f"**{nome}** está com muitas coisas na cabeça... a concentração cai, detalhes são "
        "esquecidos, regras deixam de ser seguidas. Está na hora de colocar a mente em ordem."
    )
    st.markdown(f"**Acionar compressão de memória do personagem {nome}?**")

    col_sim, col_nao = st.columns(2)
    with col_sim:
        if st.button("Sim", type="primary", use_container_width=True, key=f"btn_comprimir_sim_{nome}"):
            with st.spinner(f"{nome} organiza os pensamentos..."):
                ok, msg = GerenciadorMemoriaRPG.comprimir_memoria(nome)
            if ok:
                st.session_state.mensagem_info = (
                    f"🌬️ {nome} respira fundo, alinha os pensamentos... o foco parece ter retornado."
                )
                st.rerun()
            else:
                st.error(msg)
    with col_nao:
        if st.button("Não", use_container_width=True, key=f"btn_comprimir_nao_{nome}"):
            st.rerun()


def verificar_compressoes(agentes: list[str]):
    # Chamada no fim do app.py: abre no máximo um diálogo por execução do script.
    perguntadas = st.session_state.setdefault("compressao_perguntada", {})
    for nome in agentes:
        ctx = calcular_contexto(nome)
        if not ctx or not ctx["passou_gatilho"]:
            continue
        if perguntadas.get(nome) == ctx["medicao_id"]:
            continue
        # Marca na abertura: "Não", fechar no X ou qualquer rerun não reabrem até nova medição.
        perguntadas[nome] = ctx["medicao_id"]
        memoria_tokens = ctx["partes"].get("memoria", 0)
        memoria_util = memoria_tokens / ctx["limite"] * 100 >= LIMITE_MEMORIA_UTIL_PCT
        modal_compressao_memoria(nome, memoria_util)
        return
