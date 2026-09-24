# Título da página e cards de jogadores (avatar/iniciais, status, balão da última fala).
import streamlit as st

from fichas import obter_status_jogador, definir_status_jogador
from imagens import caminho_avatar

from ui.estado import chunked, iniciais

CSS_AVATAR = """
<div style="
    width:64px; height:64px; border-radius:10px;
    background:{cor}; color:white; display:flex;
    align-items:center; justify-content:center;
    font-weight:700; font-size:22px; margin-bottom:6px;">
    {iniciais}
</div>
"""

CSS_BALAO = """
<div style="text-align:center; font-size:16px; line-height:8px; color:{borda};">{seta}</div>
<div style="
    position:relative;
    background:{fundo};
    border:{estilo_borda} 1.5px {borda};
    border-radius:12px;
    padding:8px 10px;
    font-size:13px;
    font-style:{fonte_estilo};
    max-height:150px;
    overflow-y:auto;
    white-space:pre-wrap;
    word-wrap:break-word;">
    {texto}
</div>
"""


def renderizar_titulo_e_cards(agentes):
    st.title("🎲 Mesa de RPG — Painel do Mestre")

    if not agentes:
        st.warning("Nenhum jogador cadastrado. Adicione um jogador na barra lateral.")

    st.subheader("👥 Jogadores")

    for grupo in chunked(agentes, 4):
        cols = st.columns(len(grupo))
        for col, nome in zip(cols, grupo):
            with col:
                with st.container(border=True):
                    _renderizar_card_jogador(nome)

    st.divider()


def _renderizar_card_jogador(nome):
    status = obter_status_jogador(nome)
    cor = "#3d7a4f" if status == "vivo" else "#7a3d3d"
    foto = caminho_avatar(nome)
    if foto:
        st.image(foto, width=64)
    else:
        st.markdown(
            CSS_AVATAR.format(cor=cor, iniciais=iniciais(nome)),
            unsafe_allow_html=True,
        )
    st.markdown(f"**{nome}**")
    st.caption(f"status: {status}")

    b1, b2, b3 = st.columns(3)
    if b1.button(
        "✏️",
        key=f"btn_ficha_{nome}",
        use_container_width=True,
        help="Editar ficha",
    ):
        st.session_state.editando_ficha = nome
        st.session_state.vendo_memoria = None
        st.session_state.editando_regras = False
        st.session_state.trocando_avatar = None
        st.session_state.current_view = "mesa"
        st.rerun()
    if b2.button(
        "📜",
        key=f"btn_mem_{nome}",
        use_container_width=True,
        help="Ver memória",
    ):
        st.session_state.vendo_memoria = nome
        st.session_state.editando_ficha = None
        st.session_state.editando_regras = False
        st.session_state.trocando_avatar = None
        st.session_state.current_view = "mesa"
        st.rerun()
    if b3.button(
        "🖼️",
        key=f"btn_avatar_{nome}",
        use_container_width=True,
        help="Trocar foto",
    ):
        st.session_state.trocando_avatar = nome
        st.session_state.editando_ficha = None
        st.session_state.vendo_memoria = None
        st.session_state.editando_regras = False
        st.session_state.current_view = "mesa"
        st.rerun()

    novo_status = st.selectbox(
        "Status",
        ["vivo", "morto", "inconsciente"],
        index=(
            ["vivo", "morto", "inconsciente"].index(status)
            if status in ["vivo", "morto", "inconsciente"]
            else 0
        ),
        key=f"status_{nome}",
        label_visibility="collapsed",
    )
    if novo_status != status:
        definir_status_jogador(nome, novo_status)
        st.rerun()

    fala = st.session_state.ultima_fala.get(nome)
    if fala:
        _renderizar_balao_fala(fala)


def _renderizar_balao_fala(fala):
    aprovada = fala["aprovada"]
    privado = fala.get("privado", False)
    if privado:
        fundo, borda, estilo_borda, seta, fonte_estilo = (
            "#ede7f6",
            "#7e57c2",
            "solid",
            "💭",
            "italic",
        )
    elif aprovada:
        fundo, borda, estilo_borda, seta, fonte_estilo = (
            "#f0f2f6",
            "#c9c9c9",
            "solid",
            "▲",
            "normal",
        )
    else:
        fundo, borda, estilo_borda, seta, fonte_estilo = (
            "#fff8e1",
            "#d9a441",
            "dashed",
            "▲",
            "normal",
        )
    st.markdown(
        CSS_BALAO.format(
            fundo=fundo,
            borda=borda,
            estilo_borda=estilo_borda,
            seta=seta,
            fonte_estilo=fonte_estilo,
            texto=fala["texto"],
        ),
        unsafe_allow_html=True,
    )
    if privado:
        st.caption("💭 pensamento privado — só o mestre vê")
    elif not fala["aprovada"]:
        st.caption("⏳ aguardando aprovação do mestre")
