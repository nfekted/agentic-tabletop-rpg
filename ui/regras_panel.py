# Painel de gerenciamento de regras (múltiplos conjuntos em arquivos/regras/,
# um ativo por vez).
import streamlit as st

from fichas import (
    listar_arquivos_regras,
    obter_regra_ativa,
    carregar_regra,
    salvar_regra,
    definir_regra_ativa,
    criar_arquivo_regra,
    remover_arquivo_regra,
)

from ui.estado import indice_seguro


def renderizar_painel_regras():
    if not st.session_state.editando_regras:
        return

    st.subheader("📖 Conjuntos de regras")

    arquivos_regras = listar_arquivos_regras()
    regra_ativa = obter_regra_ativa()
    st.caption(f"Conjunto ativo agora (enviado aos jogadores): **{regra_ativa}**")

    if st.session_state.regra_selecionada not in arquivos_regras:
        st.session_state.regra_selecionada = regra_ativa

    sel = st.selectbox(
        "Selecione o conjunto para visualizar/editar",
        arquivos_regras,
        index=indice_seguro(arquivos_regras, st.session_state.regra_selecionada),
        key="select_regra_arquivo",
    )
    st.session_state.regra_selecionada = sel

    conteudo_regra = st.text_area(
        f"Conteúdo de {sel}",
        value=carregar_regra(sel),
        height=220,
        key=f"txt_regra_{sel}",
    )

    c1, c2, c3 = st.columns(3)
    if c1.button("💾 Salvar", type="primary", key=f"salvar_regra_{sel}"):
        salvar_regra(sel, conteudo_regra)
        st.session_state.mensagem_info = f"✅ '{sel}' salvo."
        st.rerun()
    if c2.button(
        "⭐ Usar agora", key=f"ativar_regra_{sel}", disabled=(sel == regra_ativa)
    ):
        definir_regra_ativa(sel)
        st.session_state.mensagem_info = f"⭐ '{sel}' passou a ser o conjunto ativo."
        st.rerun()
    if c3.button(
        "🗑️ Excluir",
        key=f"excluir_regra_{sel}",
        disabled=len(arquivos_regras) <= 1,
        help="Não é possível excluir o único conjunto de regras restante.",
    ):
        if remover_arquivo_regra(sel):
            st.session_state.regra_selecionada = None
            st.session_state.mensagem_info = f"🗑️ '{sel}' excluído."
        else:
            st.session_state.mensagem_info = "⚠️ Não foi possível excluir esse conjunto."
        st.rerun()

    st.markdown("**➕ Criar novo conjunto de regras**")
    with st.form("form_nova_regra", clear_on_submit=True):
        nome_nova_regra = st.text_input(
            "Nome (ex: combate, exploracao, social) — vira combate.txt dentro de arquivos/regras/"
        )
        criar_regra = st.form_submit_button("Criar")
        if criar_regra:
            novo_arquivo = criar_arquivo_regra(nome_nova_regra)
            if novo_arquivo:
                st.session_state.regra_selecionada = novo_arquivo
                st.session_state.mensagem_info = (
                    f"✅ '{novo_arquivo}' criado (vazio) — selecione-o acima para escrever o conteúdo."
                )
            else:
                st.session_state.mensagem_info = (
                    "⚠️ Nome inválido ou já existe um arquivo com esse nome."
                )
            st.rerun()

    if st.button("Fechar", key="fechar_regras"):
        st.session_state.editando_regras = False
        st.rerun()
    st.divider()
