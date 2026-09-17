# Painel de troca/remoção de foto (avatar) de um jogador.
import streamlit as st

from imagens import caminho_avatar, salvar_avatar_jogador, remover_avatar_jogador


def renderizar_painel_avatar():
    if not st.session_state.trocando_avatar:
        return

    nome = st.session_state.trocando_avatar
    st.subheader(f"🖼️ Foto de {nome}")

    atual = caminho_avatar(nome)
    if atual:
        st.image(atual, width=120, caption="Foto atual")
    else:
        st.caption(
            "Este jogador ainda não tem foto — está usando o quadrado com iniciais."
        )

    nova_foto = st.file_uploader(
        "Selecionar nova imagem",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"upload_avatar_{nome}",
    )
    c1, c2, c3 = st.columns(3)
    if c1.button(
        "💾 Salvar foto",
        type="primary",
        key=f"salvar_avatar_{nome}",
        disabled=nova_foto is None,
    ):
        salvar_avatar_jogador(nome, nova_foto)
        st.session_state.trocando_avatar = None
        st.session_state.mensagem_info = f"✅ Foto de {nome} atualizada."
        st.rerun()
    if c2.button(
        "🗑️ Remover foto", key=f"remover_avatar_{nome}", disabled=atual is None
    ):
        remover_avatar_jogador(nome)
        st.session_state.trocando_avatar = None
        st.session_state.mensagem_info = (
            f"🗑️ Foto de {nome} removida — voltou ao quadrado com iniciais."
        )
        st.rerun()
    if c3.button("Cancelar", key=f"cancelar_avatar_{nome}"):
        st.session_state.trocando_avatar = None
        st.rerun()
    st.divider()
