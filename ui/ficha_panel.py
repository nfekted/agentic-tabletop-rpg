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


def _limpar_estados_temporarios(nome: str, chave_status: str):
    if chave_status in st.session_state:
        del st.session_state[chave_status]
    chaves_para_remover = [
        k for k in st.session_state.keys()
        if k.startswith(f"st_nome_{nome}_")
        or k.startswith(f"st_at_{nome}_")
        or k.startswith(f"st_mx_{nome}_")
        or k.startswith(f"st_cor_{nome}_")
        or (k.startswith("txt_") and k.endswith(f"_{nome}"))
    ]
    for k in chaves_para_remover:
        del st.session_state[k]


def _executar_salvamento(nome: str, chave_status: str, sub: dict):
    status_final = []
    status_lista = st.session_state.get(chave_status, [])
    for i in range(len(status_lista)):
        n_val = st.session_state.get(f"st_nome_{nome}_{i}", status_lista[i].get("nome", "Status"))
        at_val = st.session_state.get(f"st_at_{nome}_{i}", status_lista[i].get("valor_atual", 0))
        mx_val = st.session_state.get(f"st_mx_{nome}_{i}", status_lista[i].get("valor_max", 10))
        cor_val = st.session_state.get(f"st_cor_{nome}_{i}", status_lista[i].get("cor", "#4CAF50"))
        status_final.append({
            "nome": str(n_val).strip() or "Status",
            "valor_atual": int(at_val),
            "valor_max": int(mx_val),
            "cor": str(cor_val),
        })

    novos_dados = {
        "base": st.session_state.get(f"txt_base_{nome}", sub["base"]),
        "status": status_final,
        "geral": st.session_state.get(f"txt_geral_{nome}", sub["geral"]),
        "habilidades": st.session_state.get(f"txt_hab_{nome}", sub["habilidades"]),
        "itens": st.session_state.get(f"txt_itens_{nome}", sub["itens"]),
        "personalidade": st.session_state.get(f"txt_pers_{nome}", sub["personalidade"]),
    }
    salvar_subarquivos_ficha(nome, novos_dados)

    novo_modificador = st.session_state.get(f"txt_mod_{nome}", obter_modificadores_jogador(nome))
    salvar_modificadores_jogador(nome, novo_modificador)

    _limpar_estados_temporarios(nome, chave_status)

    st.session_state.editando_ficha = None
    st.session_state.mensagem_info = f"✅ Ficha modular de {nome} salva com sucesso!"
    st.rerun()


def _cancelar_edicao(nome: str, chave_status: str):
    _limpar_estados_temporarios(nome, chave_status)
    st.session_state.editando_ficha = None
    st.rerun()


def _renderizar_botoes_acao(nome: str, chave_status: str, sub: dict, posicao: str):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("💾 Salvar ficha", type="primary", key=f"salvar_ficha_{posicao}_{nome}", use_container_width=True):
            _executar_salvamento(nome, chave_status, sub)

    with c2:
        if st.button("👁️ Ver Ficha (Prompt Consolidado)", key=f"ver_consolidado_{posicao}_{nome}", use_container_width=True):
            modal_ver_ficha(nome)

    with c3:
        if st.button("Cancelar", key=f"cancelar_ficha_{posicao}_{nome}", use_container_width=True):
            _cancelar_edicao(nome, chave_status)


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
    st.text_input(
        "Modificadores ativos (ex: Envenenado, Cego, +2 Força)",
        value=modificadores_atuais,
        key=f"txt_mod_{nome}",
        help="Substitui o antigo status de Vivo/Morto pelo campo modificadores",
    )

    # --- AÇÕES NO TOPO ---
    st.write("")
    _renderizar_botoes_acao(nome, chave_status, sub, posicao="topo")
    st.write("")

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

    # --- AÇÕES NO RODAPÉ ---
    st.write("")
    _renderizar_botoes_acao(nome, chave_status, sub, posicao="rodape")
    st.divider()
