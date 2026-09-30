# Balão de fala reutilizável (cards de jogadores e painel de turnos), com botão de fechar/restaurar
import html

import streamlit as st

CSS_SETA = '<div style="text-align:center; font-size:16px; line-height:8px; color:{borda};">{seta}</div>'

CSS_BALAO = """
<div style="
    position:relative;
    background:{fundo};
    border:{estilo_borda} 1.5px {borda};
    border-radius:12px;
    padding:{padding};
    font-size:{fonte_tamanho};
    font-style:{fonte_estilo};
    color:#31333f;
    max-height:{altura_max}px;
    overflow-y:auto;
    white-space:pre-wrap;
    word-wrap:break-word;">{texto}</div>
"""


def _estilo(fala):
    if fala.get("privado", False):
        return "#ede7f6", "#7e57c2", "solid", "💭", "italic"
    if fala["aprovada"]:
        return "#f0f2f6", "#c9c9c9", "solid", "▲", "normal"
    return "#fff8e1", "#d9a441", "dashed", "▲", "normal"


def _altura_max(texto, compacto):
    # Respostas longas ganham mais espaço antes de precisar rolar.
    tam = len(texto)
    if compacto:
        return 120 if tam <= 200 else (180 if tam <= 600 else 240)
    return 150 if tam <= 200 else (260 if tam <= 600 else 400)


def renderizar_balao_fala(nome, contexto, compacto=False, acima=False):
    #Renderiza a última fala de `nome`. `acima=True` põe o balão acima do card (seta para baixo).#
    fala = st.session_state.ultima_fala.get(nome)
    if not fala:
        return

    fechadas = st.session_state.setdefault("falas_fechadas", {})
    seq = fala.get("seq")

    # Fala fechada visualmente: só oferece restaurar (ultima_fala continua intacta).
    if nome in fechadas and fechadas[nome] == seq:
        if st.button(
            "💬 Restaurar última fala",
            key=f"btn_restaurar_fala_{contexto}_{nome}",
            type="tertiary",
        ):
            fechadas.pop(nome, None)
            st.rerun()
        return

    fundo, borda, estilo_borda, seta, fonte_estilo = _estilo(fala)
    privado = fala.get("privado", False)
    texto = fala["texto"]

    _, col_x = st.columns([8, 1])
    with col_x:
        if st.button(
            "✖",
            key=f"btn_fechar_fala_{contexto}_{nome}",
            type="tertiary",
            help="Fechar fala",
        ):
            fechadas[nome] = seq
            st.rerun()

    balao = CSS_BALAO.format(
        fundo=fundo,
        borda=borda,
        estilo_borda=estilo_borda,
        fonte_estilo=fonte_estilo,
        fonte_tamanho="12px" if compacto else "13px",
        padding="6px 8px" if compacto else "8px 10px",
        altura_max=_altura_max(texto, compacto),
        texto=html.escape(texto),
    )
    if acima:
        seta_baixo = "💭" if privado else "▼"
        st.markdown(
            balao + CSS_SETA.format(borda=borda, seta=seta_baixo),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            CSS_SETA.format(borda=borda, seta=seta) + balao, unsafe_allow_html=True
        )

    if privado:
        st.caption("💭 pensamento privado — só o mestre vê")
    elif not fala["aprovada"]:
        st.caption("⏳ aguardando aprovação do mestre")
