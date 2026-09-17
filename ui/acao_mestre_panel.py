# Painel de ação do Mestre: escolha do tipo de fala, seleção de jogadores,
# mensagem/imagem e envio.
import streamlit as st

from imagens import salvar_imagem_upload

from ui.acoes import acao_falar_com_todos, acao_falar_direcionado


def renderizar_acao_mestre(agentes):
    st.subheader("🎬 Ação do Mestre")

    tipo_acao = st.radio(
        "O que você quer fazer?",
        [
            "Falar com Todos (Público)",
            "Falar com Jogador(es) Específico(s) [Cena Pública]",
            "Cena Privada (Apenas para os Selecionados)",
        ],
        horizontal=False,
    )

    if tipo_acao == "Falar com Todos (Público)":
        selecionados = agentes
        st.caption(f"Destinatários: {', '.join(agentes) if agentes else '—'}")
    else:
        selecionados = st.multiselect("Selecione o(s) jogador(es) envolvidos", agentes)

    with st.form("form_envio_mestre", clear_on_submit=True):
        comando_mestre = st.text_area("Sua mensagem/orientação")
        imagem_upload = st.file_uploader(
            "Anexar imagem (opcional)", type=["png", "jpg", "jpeg", "webp"]
        )
        enviado = st.form_submit_button(
            "📨 Enviar",
            type="primary",
            disabled=not (bool(comando_mestre.strip()) and bool(selecionados)),
        )

    if enviado:
        caminho_imagem = salvar_imagem_upload(imagem_upload) if imagem_upload else None

        if tipo_acao == "Falar com Todos (Público)":
            acao_falar_com_todos(selecionados, comando_mestre, caminho_imagem)
        elif tipo_acao == "Falar com Jogador(es) Específico(s) [Cena Pública]":
            acao_falar_direcionado(selecionados, False, comando_mestre, caminho_imagem)
        else:
            acao_falar_direcionado(selecionados, True, comando_mestre, caminho_imagem)

        st.rerun()

    st.divider()
