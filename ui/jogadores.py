# Título da página e cards de jogadores (avatar/iniciais, modificadores, barras de status, balão da última fala).
import streamlit as st

from config import obter_modificadores_jogador
from fichas import carregar_status_jogador
from imagens import caminho_avatar

from ui.estado import chunked, iniciais
from ui.ficha_panel import modal_ver_ficha
from turno import turno_ativo, iniciar_turno
from ui.turno_panel import renderizar_painel_turnos

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
    if turno_ativo():
        renderizar_painel_turnos(agentes)
        return

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

    st.write("")
    if st.button("⚔️ Iniciar Modo por Turnos", type="secondary", use_container_width=True, key="btn_iniciar_turnos"):
        iniciar_turno(agentes)
        st.rerun()

    st.divider()


def _renderizar_card_jogador(nome):
    foto = caminho_avatar(nome)
    if foto:
        st.image(foto, width=64)
    else:
        st.markdown(
            CSS_AVATAR.format(cor="#2c3e50", iniciais=iniciais(nome)),
            unsafe_allow_html=True,
        )

    st.markdown(f"**{nome}**")

    # Modificadores substituindo o antigo status de Vivo/Morto
    mods = obter_modificadores_jogador(nome)
    st.caption(f"modificadores: {mods}" if mods else "modificadores: nenhum")

    # Barras de status visuais
    status_lista = carregar_status_jogador(nome)
    if status_lista:
        html_barras = []
        for st_item in status_lista:
            st_nome = st_item.get("nome", "Status")
            atual = st_item.get("valor_atual", 0)
            maximo = st_item.get("valor_max", 1)
            cor = st_item.get("cor", "#DC143C")
            pct = max(0, min(100, int((atual / maximo * 100) if maximo > 0 else 0)))
            html_barras.append(f"""
            <div style="margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; font-weight:600; margin-bottom:2px; color:inherit;">
                    <span>{st_nome}</span>
                    <span>{atual}/{maximo}</span>
                </div>
                <div style="background:rgba(128,128,128,0.25); border-radius:4px; height:8px; overflow:hidden; width:100%;">
                    <div style="background:{cor}; width:{pct}%; height:100%; border-radius:4px;"></div>
                </div>
            </div>
            """)
        st.markdown("".join(html_barras), unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    if b1.button(
        "✏️",
        key=f"btn_ficha_{nome}",
        use_container_width=True,
        help="Editar ficha modular",
    ):
        st.session_state.editando_ficha = nome
        st.session_state.vendo_memoria = None
        st.session_state.editando_regras = False
        st.session_state.trocando_avatar = None
        st.session_state.current_view = "mesa"
        st.rerun()

    if b2.button(
        "👁️",
        key=f"btn_ver_{nome}",
        use_container_width=True,
        help="Ver ficha consolidada (somente leitura)",
    ):
        modal_ver_ficha(nome)

    if b3.button(
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

    if b4.button(
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
