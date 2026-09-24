# Painel de edição e visualização de ficha modular de um jogador.
import streamlit as st

from config import obter_modificadores_jogador, salvar_modificadores_jogador
from fichas import (
    carregar_ficha,
    carregar_subarquivos_ficha,
    salvar_subarquivos_ficha,
)


@st.dialog("👁️ Ficha Consolidada", width='large')
def modal_ver_ficha(nome: str):
    st.caption(f"Ficha final compilado para o agente **{nome}** (somente leitura):")
    prompt_completo = carregar_ficha(nome)
    st.markdown(prompt_completo)
    if st.button("Fechar", use_container_width=True):
        st.rerun()


def renderizar_painel_ficha():
    if not st.session_state.editando_ficha:
        return

    nome = st.session_state.editando_ficha
    sub = carregar_subarquivos_ficha(nome)

    st.subheader(f"✏️ Editando Ficha Modular de {nome}")

    chave_status = f"editor_status_{nome}"
    if chave_status not in st.session_state:
        st.session_state[chave_status] = [dict(s) for s in sub["status"]]

    # Campo de Modificadores (conforme especificação do jogadores.json)
    modificadores_atuais = obter_modificadores_jogador(nome)
    novo_modificador = st.text_input(
        "Modificadores ativos (ex: Envenenado, Cego, +2 Força)",
        value=modificadores_atuais,
        key=f"txt_mod_{nome}",
        help="Substitui o antigo status de Vivo/Morto pelo campo modificadores",
    )

    # --- GRID 2 COLUNAS X 3 LINHAS ---

    # Linha 1: 1. Base | 2. Status
    col1_1, col1_2 = st.columns(2)
    with col1_1:
        st.markdown("#### 1. Base")
        base_conteudo = st.text_area(
            "Informações Básicas",
            value=sub["base"],
            height=280,
            key=f"txt_base_{nome}",
            label_visibility="collapsed",
        )

    with col1_2:
        st.markdown("#### 2. Status")
        with st.container(border=True, height=280):
            status_lista = st.session_state[chave_status]
            if not status_lista:
                st.caption("Nenhum status configurado.")

            indices_para_remover = []
            c_n, c_at, c_mx, c_cor, c_del = st.columns([3, 2, 2, 1, 1])
            with c_n:
                st.caption("Nome")
            with c_at:
                st.caption("Atual")
            with c_mx:
                st.caption("Máximo")
            with c_cor:
                st.caption("Cor barra")
            for i, st_item in enumerate(status_lista):
                c_n, c_at, c_mx, c_cor, c_del = st.columns([3, 2, 2, 1, 1])
                with c_n:
                    st.text_input(
                        "Nome",
                        value=st_item.get("nome", "Status"),
                        key=f"st_nome_{nome}_{i}",
                        placeholder="Nome",
                        label_visibility="collapsed",
                    )
                with c_at:
                    st.number_input(
                        "Atual",
                        value=int(st_item.get("valor_atual", 0)),
                        key=f"st_at_{nome}_{i}",
                        step=1,
                        label_visibility="collapsed",
                    )
                with c_mx:
                    st.number_input(
                        "Máx",
                        value=int(st_item.get("valor_max", 10)),
                        key=f"st_mx_{nome}_{i}",
                        step=1,
                        label_visibility="collapsed",
                    )
                with c_cor:
                    st.color_picker(
                        "Cor",
                        value=st_item.get("cor", "#DC143C"),
                        key=f"st_cor_{nome}_{i}",
                        label_visibility="collapsed",
                    )
                with c_del:
                    if st.button("🗑️", key=f"st_del_{nome}_{i}", help="Remover este status"):
                        indices_para_remover.append(i)

            if indices_para_remover:
                for idx in sorted(indices_para_remover, reverse=True):
                    st.session_state[chave_status].pop(idx)
                st.rerun()

            if st.button("➕ Adicionar Novo Status", key=f"btn_add_st_{nome}"):
                st.session_state[chave_status].append({
                    "nome": "Novo Status",
                    "valor_atual": 10,
                    "valor_max": 10,
                    "cor": "#4CAF50",
                })
                st.rerun()

    # Linha 2: 3. Geral | 4. Habilidades
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        st.markdown("#### 3. Geral")
        geral_conteudo = st.text_area(
            "Atributos e Perícias",
            value=sub["geral"],
            height=250,
            key=f"txt_geral_{nome}",
            label_visibility="collapsed",
        )

    with col2_2:
        st.markdown("#### 4. Habilidades")
        habilidades_conteudo = st.text_area(
            "Habilidades, Poderes e Passivas",
            value=sub["habilidades"],
            height=250,
            key=f"txt_hab_{nome}",
            label_visibility="collapsed",
        )

    # Linha 3: 5. Itens | 6. Personalidade
    col3_1, col3_2 = st.columns(2)
    with col3_1:
        st.markdown("#### 5. Itens")
        itens_conteudo = st.text_area(
            "Equipamentos e Mochila",
            value=sub["itens"],
            height=250,
            key=f"txt_itens_{nome}",
            label_visibility="collapsed",
        )

    with col3_2:
        st.markdown("#### 6. Personalidade")
        personalidade_conteudo = st.text_area(
            "Regras de Interpretação e Roleplay",
            value=sub["personalidade"],
            height=250,
            key=f"txt_pers_{nome}",
            label_visibility="collapsed",
        )

    # --- AÇÕES DO PAINEL ---
    st.write("")
    c4, c5, c6 = st.columns([1, 1, 1])
    with c4:
        if st.button("💾 Salvar ficha", type="primary", key=f"salvar_ficha_{nome}", use_container_width=True):
            # Coleta status atualizados
            status_final = []
            for i in range(len(st.session_state[chave_status])):
                n_val = st.session_state.get(f"st_nome_{nome}_{i}", st.session_state[chave_status][i].get("nome", "Status"))
                at_val = st.session_state.get(f"st_at_{nome}_{i}", st.session_state[chave_status][i].get("valor_atual", 0))
                mx_val = st.session_state.get(f"st_mx_{nome}_{i}", st.session_state[chave_status][i].get("valor_max", 10))
                cor_val = st.session_state.get(f"st_cor_{nome}_{i}", st.session_state[chave_status][i].get("cor", "#4CAF50"))
                status_final.append({
                    "nome": str(n_val).strip() or "Status",
                    "valor_atual": int(at_val),
                    "valor_max": int(mx_val),
                    "cor": str(cor_val),
                })

            novos_dados = {
                "base": base_conteudo,
                "status": status_final,
                "geral": geral_conteudo,
                "habilidades": habilidades_conteudo,
                "itens": itens_conteudo,
                "personalidade": personalidade_conteudo,
            }
            salvar_subarquivos_ficha(nome, novos_dados)
            salvar_modificadores_jogador(nome, novo_modificador)

            if chave_status in st.session_state:
                del st.session_state[chave_status]

            st.session_state.editando_ficha = None
            st.session_state.mensagem_info = f"✅ Ficha modular de {nome} salva com sucesso!"
            st.rerun()

    with c5:
        if st.button("👁️ Ver Ficha (Prompt Consolidado)", key=f"ver_consolidado_{nome}", use_container_width=True):
            modal_ver_ficha(nome)

    with c6:
        if st.button("Cancelar", key=f"cancelar_ficha_{nome}", use_container_width=True):
            if chave_status in st.session_state:
                del st.session_state[chave_status]
            st.session_state.editando_ficha = None
            st.rerun()

    st.divider()
