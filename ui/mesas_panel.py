# Modal "Salvar / Restaurar Mesa": backup e restauração de arquivos/ + tokens/ em mesas/*.zip
import time

import streamlit as st

from mesas_manager import (
    info_mesa,
    listar_mesas,
    mesa_existe,
    restaurar_mesa,
    salvar_mesa,
)

AVISO_API_KEY = (
    "🔑 A chave da API (config.json) **não** é incluída no arquivo. "
    "Guarde-a em local seguro ou reconfigure a LLM ao restaurar."
)
CHAVE_CONFIRMAR = "_mesa_confirmar"


def _rotulo_mesa(nome: str) -> str:
    try:
        mtime, tamanho = info_mesa(nome)
        data = time.strftime("%d/%m/%Y %H:%M", time.localtime(mtime))
        return f"{nome}  ({data}, {tamanho / 1024:.0f} KB)"
    except OSError:
        return nome


def _restaurar_e_recarregar(nome: str):
    ok, msg = restaurar_mesa(nome)
    if not ok:
        st.error(msg)
        return
    # "Reload": limpa a sessão inteira; inicializar_estado refaz os defaults e a tela relê o disco.
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]
    st.session_state.mensagem_info = (
        f"✅ Mesa '{nome}' restaurada. Reconfigure a chave da API se necessário."
    )
    st.rerun()


@st.dialog("💾 Salvar / Restaurar Mesa", width="large")
def modal_salvar_restaurar_mesa():
    col_rest, col_salvar = st.columns(2)

    with col_rest:
        with st.container(border=True):
            st.subheader("♻️ Restaurar mesa")
            mesas = listar_mesas()
            if not mesas:
                st.caption("Nenhuma mesa salva na pasta mesas/.")
            else:
                sel = st.selectbox(
                    "Mesa salva",
                    mesas,
                    format_func=_rotulo_mesa,
                    key="sel_mesa_restaurar",
                )
                if st.button("♻️ Restaurar", use_container_width=True, key="btn_restaurar_mesa"):
                    st.session_state[CHAVE_CONFIRMAR] = sel

                alvo = st.session_state.get(CHAVE_CONFIRMAR)
                if alvo:
                    st.warning(
                        f"Deseja restaurar a mesa **{alvo}**? "
                        "Os dados da mesa atual serão sobrescritos."
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(
                            "Confirmar",
                            type="primary",
                            use_container_width=True,
                            key="btn_confirmar_restaurar_mesa",
                        ):
                            st.session_state.pop(CHAVE_CONFIRMAR, None)
                            _restaurar_e_recarregar(alvo)
                    with c2:
                        if st.button(
                            "Cancelar",
                            use_container_width=True,
                            key="btn_cancelar_restaurar_mesa",
                        ):
                            st.session_state.pop(CHAVE_CONFIRMAR, None)
                            st.rerun()
            st.caption(AVISO_API_KEY)

    with col_salvar:
        with st.container(border=True):
            st.subheader("💾 Salvar mesa")
            nome = st.text_input(
                "Nome da mesa",
                placeholder="Ex: Campanha_Sessao_03",
                key="nome_nova_mesa",
            )
            if nome.strip() and mesa_existe(nome.strip()):
                st.warning("Já existe uma mesa com esse nome — ela será sobrescrita.")
            if st.button(
                "💾 Salvar",
                type="primary",
                use_container_width=True,
                key="btn_salvar_mesa",
            ):
                ok, msg = salvar_mesa(nome)
                (st.success if ok else st.error)(msg)
            st.caption(AVISO_API_KEY)
