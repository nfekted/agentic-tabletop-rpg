# Painel visual do Modo por Turnos / Gestão de Cenas e Combate
import streamlit as st

from config import obter_modificadores_jogador
from fichas import carregar_status_jogador
from imagens import caminho_avatar
from tokens_manager import CATEGORIAS, listar_tokens
from turno import (
    adicionar_area,
    adicionar_token_ao_turno,
    atualizar_ficha_token,
    atualizar_ordem_participante,
    avancar_proxima_acao,
    carregar_turno,
    desvincular_participante,
    encerrar_turno,
    obter_area_do_participante,
    obter_participante_por_ordem,
    remover_area,
    remover_token_do_turno,
    sincronizar_personagens,
    verificar_empates,
    vincular_participante,
)
from ui.estado import iniciais

CSS_MINI_AVATAR = """
<div style="
    width:42px; height:42px; border-radius:8px;
    background:{cor}; color:white; display:flex;
    align-items:center; justify-content:center;
    font-weight:700; font-size:16px; margin-bottom:4px;">
    {iniciais}
</div>
"""


@st.dialog("👁️ Ficha do Token (Cópia no Combate)", width="large")
def modal_ficha_token(token_id: str):
    turno_dados = carregar_turno()
    if not turno_dados:
        st.warning("Combate não está ativo.")
        return

    tok = next((t for t in turno_dados.get("tokens", []) if t["id"] == token_id), None)
    if not tok:
        st.error("Token não encontrado.")
        return

    icone = tok.get("tipo_icone", "👾")
    nome_exib = tok.get("nome_exibicao", "Token")
    st.subheader(f"{icone} {nome_exib}")
    st.caption("Esta ficha é uma cópia isolada do combate atual. Modificações aqui não afetam o arquivo original.")

    ficha_dados = tok.get("ficha_dados", {})
    conteudo_atual = ficha_dados.get("conteudo", "")

    novo_conteudo = st.text_area(
        "Anotações / Ficha do Token:",
        value=conteudo_atual,
        height=320,
        key=f"txt_token_modal_{token_id}",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Salvar no Combate", type="primary", use_container_width=True, key=f"btn_salvar_tok_{token_id}"):
            ficha_dados["conteudo"] = novo_conteudo
            atualizar_ficha_token(token_id, ficha_dados)
            st.session_state.mensagem_info = f"✅ Ficha de {nome_exib} atualizada no combate!"
            st.rerun()

    with col2:
        if st.button("Fechar", use_container_width=True, key=f"btn_fechar_tok_{token_id}"):
            st.rerun()


def _ao_mudar_ordem(participante_id: str, chave_session: str):
    novo_valor = st.session_state.get(chave_session)
    atualizar_ordem_participante(participante_id, novo_valor)


def _renderizar_card_personagem_compacto(p_dict: dict, turno_dados: dict, dentro_area: bool = False):
    nome = p_dict["nome"]
    p_id = p_dict["id"]
    ordem = p_dict.get("ordem")
    ordem_atual = turno_dados.get("ordem_atual")
    em_andamento = turno_dados.get("em_andamento", False)
    eh_sua_vez = (em_andamento and ordem is not None and ordem == ordem_atual)

    estilo_borda = "border: 2px solid #e74c3c; background: rgba(231, 76, 60, 0.08);" if eh_sua_vez else ""
    with st.container(border=True):
        if eh_sua_vez:
            st.markdown(
                '<div style="background:#e74c3c; color:white; font-size:11px; font-weight:700; text-align:center; border-radius:4px; padding:2px 4px; margin-bottom:4px;">🔥 SUA VEZ</div>',
                unsafe_allow_html=True,
            )

        col_img, col_info = st.columns([1, 3])
        with col_img:
            foto = caminho_avatar(nome)
            if foto:
                st.image(foto, width=44)
            else:
                st.markdown(
                    CSS_MINI_AVATAR.format(cor="#2c3e50", iniciais=iniciais(nome)),
                    unsafe_allow_html=True,
                )

        with col_info:
            st.markdown(f"**{nome}**")
            mods = obter_modificadores_jogador(nome)
            if mods:
                st.caption(f"mods: {mods}")

        # Barras de status compactas
        status_lista = carregar_status_jogador(nome)
        if status_lista:
            html_barras = []
            for st_item in status_lista[:3]:  # Exibe os 3 principais
                st_nome = st_item.get("nome", "Status")
                atual = st_item.get("valor_atual", 0)
                maximo = st_item.get("valor_max", 1)
                cor = st_item.get("cor", "#DC143C")
                pct = max(0, min(100, int((atual / maximo * 100) if maximo > 0 else 0)))
                html_barras.append(f"""
                <div style="margin-bottom:3px;">
                    <div style="display:flex; justify-content:space-between; font-size:10px; font-weight:600; margin-bottom:1px;">
                        <span>{st_nome}</span>
                        <span>{atual}/{maximo}</span>
                    </div>
                    <div style="background:rgba(128,128,128,0.25); border-radius:3px; height:5px; overflow:hidden; width:100%;">
                        <div style="background:{cor}; width:{pct}%; height:100%; border-radius:3px;"></div>
                    </div>
                </div>
                """)
            st.markdown("".join(html_barras), unsafe_allow_html=True)

        # Campo de Ordem
        travado = em_andamento and (ordem is not None and ordem > 0)
        sufixo_key = f"{p_id}_{'area' if dentro_area else 'solto'}"
        chave_ordem = f"ordem_input_{sufixo_key}"

        col_ord, col_act = st.columns([2, 1])
        with col_ord:
            st.number_input(
                "Ordem",
                min_value=1,
                step=1,
                value=int(ordem) if (ordem is not None and ordem > 0) else 1,
                key=chave_ordem,
                disabled=travado,
                help="Ordem de iniciativa no combate. Fica travada durante a rodada.",
                on_change=_ao_mudar_ordem,
                args=(p_id, chave_ordem),
            )
            # Atualiza caso o usuário ainda não tenha submetido
            if ordem is None and chave_ordem in st.session_state:
                atualizar_ordem_participante(p_id, st.session_state[chave_ordem])

        with col_act:
            st.write("")
            if st.button("✏️", key=f"btn_ficha_compacta_{sufixo_key}", help="Editar ficha"):
                st.session_state.editando_ficha = nome
                st.session_state.current_view = "mesa"
                st.rerun()

        if dentro_area:
            if st.button("❌ Remover da Área", key=f"btn_remover_area_{sufixo_key}", use_container_width=True):
                desvincular_participante(p_id)
                st.rerun()


def _renderizar_card_token_compacto(tok_dict: dict, turno_dados: dict, dentro_area: bool = False):
    tok_id = tok_dict["id"]
    nome_exib = tok_dict.get("nome_exibicao", "Token")
    icone = tok_dict.get("tipo_icone", "👾")
    ordem = tok_dict.get("ordem")
    ordem_atual = turno_dados.get("ordem_atual")
    em_andamento = turno_dados.get("em_andamento", False)
    eh_sua_vez = (em_andamento and ordem is not None and ordem == ordem_atual)

    with st.container(border=True):
        if eh_sua_vez:
            st.markdown(
                '<div style="background:#e74c3c; color:white; font-size:11px; font-weight:700; text-align:center; border-radius:4px; padding:2px 4px; margin-bottom:4px;">🔥 SUA VEZ</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"### {icone} {nome_exib}")

        travado = em_andamento and (ordem is not None and ordem > 0)
        sufixo_key = f"{tok_id}_{'area' if dentro_area else 'solto'}"
        chave_ordem = f"ordem_input_tok_{sufixo_key}"

        col_ord, col_act = st.columns([2, 1])
        with col_ord:
            st.number_input(
                "Ordem",
                min_value=1,
                step=1,
                value=int(ordem) if (ordem is not None and ordem > 0) else 1,
                key=chave_ordem,
                disabled=travado,
                help="Ordem de iniciativa deste token.",
                on_change=_ao_mudar_ordem,
                args=(tok_id, chave_ordem),
            )
            if ordem is None and chave_ordem in st.session_state:
                atualizar_ordem_participante(tok_id, st.session_state[chave_ordem])

        with col_act:
            st.write("")
            if st.button("👁️", key=f"btn_ver_tok_{sufixo_key}", help="Ver / Editar ficha do token"):
                modal_ficha_token(tok_id)

        col_del1, col_del2 = st.columns(2) if dentro_area else (None, None)
        if dentro_area:
            if st.button("❌ Remover da Área", key=f"btn_remover_area_tok_{sufixo_key}", use_container_width=True):
                desvincular_participante(tok_id)
                st.rerun()
        else:
            if st.button("🗑️ Remover da Cena", key=f"btn_del_tok_{sufixo_key}", use_container_width=True):
                remover_token_do_turno(tok_id)
                st.rerun()


def renderizar_painel_turnos(agentes: list[str]):
    turno_dados = sincronizar_personagens(agentes)
    if not turno_dados:
        st.error("Erro ao carregar os dados de combate.")
        return

    em_andamento = turno_dados.get("em_andamento", False)
    ordem_atual = turno_dados.get("ordem_atual")

    # --- BARRA DE CONTROLE SUPERIOR ---
    st.title("⚔️ Gestão de Cenas e Combate — Modo por Turnos")

    participante_ativo = obter_participante_por_ordem(turno_dados, ordem_atual) if ordem_atual else None
    nome_ativo = (participante_ativo.get("nome") or participante_ativo.get("nome_exibicao")) if participante_ativo else "Nenhum"

    col_status, col_btn_prox, col_btn_fim = st.columns([3, 2, 2])
    with col_status:
        if not em_andamento:
            st.info("🟡 **Em Preparação**: Defina a ordem dos participantes e posicione-os nas áreas.")
        else:
            st.success(f"🟢 **Combate Ativo** — Vez de: **{nome_ativo}** (Ordem #{ordem_atual})")

    empates = verificar_empates(turno_dados)
    if empates:
        st.warning(f"⚠️ **Empate de Ordem**: A(s) ordem(ns) **{', '.join(map(str, empates))}** está(ão) repetida(s)! Defina ordens distintas.")

    with col_btn_prox:
        rotulo_prox = "🚀 Iniciar Combate" if not em_andamento else "▶️ Próxima Ação"
        if st.button(rotulo_prox, type="primary", use_container_width=True, key="btn_proxima_acao", disabled=bool(empates)):
            sucesso, msg = avancar_proxima_acao(turno_dados)
            if sucesso:
                st.session_state.mensagem_info = msg
            else:
                st.warning(msg)
            st.rerun()

    with col_btn_fim:
        if st.button("🛑 Encerrar Modo por Turnos", use_container_width=True, key="btn_encerrar_turno"):
            encerrar_turno()
            st.session_state.mensagem_info = "🏁 Modo por Turnos encerrado com sucesso."
            st.rerun()

    st.divider()

    # Mapeamento de participantes em áreas
    ids_em_areas = set()
    for a in turno_dados.get("areas", []):
        for pid in a.get("participantes", []):
            ids_em_areas.add(pid)

    personagens_soltos = [p for p in turno_dados.get("personagens", []) if p["id"] not in ids_em_areas]
    tokens_soltos = [t for t in turno_dados.get("tokens", []) if t["id"] not in ids_em_areas]

    # --- GRID DE 3 PAINÉIS (Esquerda: Personagens, Centro: Áreas, Direita: Tokens) ---
    col_personagens, col_areas, col_tokens = st.columns([1, 1.3, 1])

    # 1. PAINEL ESQUERDO: Personagens (Sem Área)
    with col_personagens:
        st.subheader(f"👥 Personagens ({len(personagens_soltos)})")
        st.caption("Participantes jogadores não vinculados a áreas específicas.")

        if not personagens_soltos:
            st.caption("Todos os personagens estão alocados em áreas da cena.")

        for p in personagens_soltos:
            _renderizar_card_personagem_compacto(p, turno_dados, dentro_area=False)

    # 2. PAINEL CENTRAL: Áreas da Cena
    with col_areas:
        st.subheader("📍 Áreas da Cena")
        st.caption("Posicione participantes em zonas de combate ou ambientes.")

        # Criar nova área
        with st.expander("➕ Adicionar Nova Área"):
            with st.form("form_nova_area", clear_on_submit=True):
                nome_area = st.text_input("Nome da Área", placeholder="Ex: Entrada, Frente da Taverna, Salão...")
                btn_add_area = st.form_submit_button("Criar Área")
                if btn_add_area and nome_area.strip():
                    adicionar_area(nome_area.strip())
                    st.rerun()

        areas = turno_dados.get("areas", [])
        if not areas:
            st.info("Nenhuma área criada. Adicione uma área acima para organizar a cena.")

        # Dicionários rápidos para lookup de participantes
        todos_personagens_dict = {p["id"]: p for p in turno_dados.get("personagens", [])}
        todos_tokens_dict = {t["id"]: t for t in turno_dados.get("tokens", [])}

        for area in areas:
            area_id = area["id"]
            area_nome = area["nome"]
            participantes_ids = area.get("participantes", [])

            with st.container(border=True):
                cab_col1, cab_col2 = st.columns([4, 1])
                with cab_col1:
                    st.markdown(f"#### 📍 {area_nome} ({len(participantes_ids)})")
                with cab_col2:
                    if st.button("🗑️", key=f"btn_del_area_{area_id}", help="Excluir esta área"):
                        remover_area(area_id)
                        st.rerun()

                # Vínculo de participantes
                disponiveis = []
                for p in turno_dados.get("personagens", []):
                    if p["id"] not in participantes_ids:
                        disponiveis.append((p["id"], f"👤 {p['nome']}"))
                for t in turno_dados.get("tokens", []):
                    if t["id"] not in participantes_ids:
                        disponiveis.append((t["id"], f"{t.get('tipo_icone', '👾')} {t.get('nome_exibicao', 'Token')}"))

                if disponiveis:
                    col_sel_part, col_btn_vinc = st.columns([3, 2])
                    with col_sel_part:
                        sel_id = st.selectbox(
                            "Vincular participante:",
                            options=[d[0] for d in disponiveis],
                            format_func=lambda x: next((d[1] for d in disponiveis if d[0] == x), x),
                            key=f"sel_vinc_{area_id}",
                            label_visibility="collapsed",
                        )
                    with col_btn_vinc:
                        if st.button("+ Vincular", key=f"btn_vinc_{area_id}", use_container_width=True):
                            vincular_participante(area_id, sel_id)
                            st.rerun()

                st.write("")
                # Renderiza minicards dentro da área
                if not participantes_ids:
                    st.caption("Nenhum participante nesta área.")
                else:
                    for pid in participantes_ids:
                        if pid in todos_personagens_dict:
                            _renderizar_card_personagem_compacto(todos_personagens_dict[pid], turno_dados, dentro_area=True)
                        elif pid in todos_tokens_dict:
                            _renderizar_card_token_compacto(todos_tokens_dict[pid], turno_dados, dentro_area=True)

    # 3. PAINEL DIREITO: Tokens da Cena (Sem Área)
    with col_tokens:
        st.subheader(f"👾 Tokens da Cena ({len(tokens_soltos)})")
        st.caption("Inimigos, NPCs e Itens com cópias isoladas no turno.")

        with st.expander("➕ Adicionar Token à Cena"):
            cat_sel = st.selectbox("Categoria:", options=["inimigo", "npc", "item"], format_func=lambda x: CATEGORIAS.get(x, x))
            arquivos_cat = listar_tokens(cat_sel)
            if arquivos_cat:
                arq_sel = st.selectbox("Token disponível:", arquivos_cat)
                if st.button("Adicionar à Cena", type="primary", use_container_width=True, key="btn_add_tok_cena"):
                    adicionar_token_ao_turno(cat_sel, arq_sel)
                    st.rerun()
            else:
                st.caption(f"Nenhum arquivo em tokens/{cat_sel}/. Crie tokens na aba Tokens.")

        if not tokens_soltos:
            st.caption("Nenhum token solto na cena.")

        for t in tokens_soltos:
            _renderizar_card_token_compacto(t, turno_dados, dentro_area=False)
