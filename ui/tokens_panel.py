# Painel visual para Gerenciamento de Inimigos, Itens e NPCs (CRUD de tokens em /tokens)
import streamlit as st

from tokens_manager import (
    CATEGORIAS,
    garantir_estrutura_tokens,
    listar_tokens,
    carregar_token,
    salvar_token,
    criar_token,
    excluir_token,
)
from ui.estado import indice_seguro


def _renderizar_aba_categoria(categoria: str, rotulo_singular: str, icone: str):
    garantir_estrutura_tokens()
    arquivos = listar_tokens(categoria)

    st.markdown(f"### {icone} {CATEGORIAS[categoria]} (`tokens/{categoria}/`)")

    if arquivos:
        chave_sel = f"token_sel_{categoria}"
        arquivo_atual = st.session_state.get(chave_sel)
        if arquivo_atual not in arquivos:
            arquivo_atual = arquivos[0]
            st.session_state[chave_sel] = arquivo_atual

        col_sel, col_info = st.columns([3, 1])
        with col_sel:
            sel = st.selectbox(
                f"Selecione um(a) {rotulo_singular.lower()}:",
                arquivos,
                index=indice_seguro(arquivos, arquivo_atual),
                key=f"select_token_{categoria}",
            )
            st.session_state[chave_sel] = sel

        with col_info:
            st.caption(f"📁 Total: **{len(arquivos)}** arquivo(s)")

        conteudo_original = carregar_token(categoria, sel)
        conteudo_editado = st.text_area(
            f"Ficha / Anotações de {sel}:",
            value=conteudo_original,
            height=280,
            key=f"txt_token_{categoria}_{sel}",
        )

        col_btn1, col_btn2, _ = st.columns([1, 1, 3])
        with col_btn1:
            if st.button(
                "💾 Salvar",
                type="primary",
                key=f"salvar_{categoria}_{sel}",
                use_container_width=True,
            ):
                salvar_token(categoria, sel, conteudo_editado)
                st.session_state.mensagem_info = (
                    f"✅ '{sel}' salvo com sucesso em tokens/{categoria}/."
                )
                st.rerun()

        with col_btn2:
            if st.button(
                "🗑️ Excluir", key=f"excluir_{categoria}_{sel}", use_container_width=True
            ):
                if excluir_token(categoria, sel):
                    st.session_state[chave_sel] = None
                    st.session_state.mensagem_info = (
                        f"🗑️ '{sel}' excluído de tokens/{categoria}/."
                    )
                else:
                    st.session_state.mensagem_info = (
                        f"⚠️ Não foi possível excluir '{sel}'."
                    )
                st.rerun()
    else:
        st.info(
            f"Nenhum arquivo encontrado em `tokens/{categoria}/`. Crie o primeiro abaixo!"
        )

    st.markdown("---")
    st.markdown(f"**➕ Criar novo(a) {rotulo_singular}**")
    with st.form(f"form_novo_{categoria}", clear_on_submit=True):
        nome_novo = st.text_input(
            f"Nome do {rotulo_singular.lower()}",
            placeholder=f"Ex: {('esqueleto' if categoria == 'inimigo' else 'ferreiro' if categoria == 'npc' else 'pocao_cura')}",
            help="O nome será salvo como arquivo .txt dentro da pasta tokens/"
            + categoria
            + "/",
        )
        conteudo_novo = st.text_area(
            "Conteúdo inicial (opcional)",
            height=120,
            placeholder="Digite detalhes, atributos, história ou anotações...",
        )
        btn_criar = st.form_submit_button("Criar")
        if btn_criar:
            novo_arquivo = criar_token(categoria, nome_novo, conteudo_novo)
            if novo_arquivo:
                st.session_state[f"token_sel_{categoria}"] = novo_arquivo
                st.session_state.mensagem_info = (
                    f"✅ '{novo_arquivo}' criado em tokens/{categoria}/!"
                )
            else:
                st.session_state.mensagem_info = (
                    "⚠️ Nome inválido ou arquivo já existente."
                )
            st.rerun()


def renderizar_painel_tokens():
    # Painel principal para gerenciamento e CRUD simples de arquivos .txt em /tokens.
    garantir_estrutura_tokens()

    col_titulo, col_fechar = st.columns([4, 1])
    with col_titulo:
        st.header("👾 Gerenciar Inimigos, Itens e NPCs")
        st.caption(
            "Anotações e fichas em texto simples (.txt) organizadas na pasta `/tokens`."
        )
    with col_fechar:
        if st.button(
            "⬅️ Voltar para a Mesa",
            key="btn_voltar_mesa",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.current_view = "mesa"
            st.rerun()

    st.divider()

    tab_inimigos, tab_npcs, tab_itens = st.tabs(
        [
            "⚔️ Inimigos (tokens/inimigo/)",
            "👤 NPCs (tokens/npc/)",
            "🎒 Itens (tokens/item/)",
        ]
    )

    with tab_inimigos:
        _renderizar_aba_categoria("inimigo", "Inimigo", "⚔️")

    with tab_npcs:
        _renderizar_aba_categoria("npc", "NPC", "👤")

    with tab_itens:
        _renderizar_aba_categoria("item", "Item", "🎒")

    st.divider()
    if st.button("⬅️ Voltar para a Mesa", key="btn_voltar_mesa_rodape"):
        st.session_state.current_view = "mesa"
        st.rerun()
