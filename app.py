# Interface visual (Streamlit) para o Mestre conduzir a mesa de RPG
import streamlit as st

from config import carregar_agentes, adicionar_agente
from fichas import (
    listar_arquivos_regras,
    obter_regra_ativa,
    carregar_regra,
    salvar_regra,
    definir_regra_ativa,
    criar_arquivo_regra,
    remover_arquivo_regra,
    carregar_ficha,
    salvar_ficha,
    obter_status_jogador,
    definir_status_jogador,
)
from imagens import (
    salvar_imagem_upload,
    caminho_avatar,
    salvar_avatar_jogador,
    remover_avatar_jogador,
)
from memoria import obter_pasta_agente, obter_arquivos_memoria, GerenciadorMemoriaRPG
from agentes import gerar_resposta_agente
from tags import (
    extrair_tags_resposta,
    formatar_conteudo_publico,
    formatar_para_autor,
    tem_acao,
    tem_duvida,
    tem_pensamento,
    apenas_pensamento,
)

st.set_page_config(page_title="Mesa de RPG — Painel do Mestre", layout="wide")


# ----------------------------------------------------------------------------
# ESTADO DA SESSÃO
# ----------------------------------------------------------------------------
def inicializar_estado():
    padrao = {
        "historico": [],
        "rodada_ativa": False,
        "envolvidos_rodada_atual": set(),
        "editando_regras": False,
        "regra_selecionada": None,
        "editando_ficha": None,
        "vendo_memoria": None,
        "pending_principal": None,
        "aguardando_redirect": None,
        "pending_redirects": [],
        "mensagem_info": None,
        "ultima_fala": {},
        "trocando_avatar": None,
    }
    for chave, valor in padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


inicializar_estado()

for ag in carregar_agentes():
    obter_pasta_agente(ag)


def registrar_fala(
    agente: str, texto: str, aprovada: bool = True, privado: bool = False
):
    # Guarda a última fala de um agente para exibir como balão junto ao seu card.
    st.session_state.ultima_fala[agente] = {
        "texto": texto,
        "aprovada": aprovada,
        "privado": privado,
    }


def limpar_fala(agente: str):
    st.session_state.ultima_fala.pop(agente, None)


def eh_pensamento(resposta: str) -> bool:
    return "[pensamento]" in resposta.lower()


def salvar_pensamento_privado(agente: str, resposta: str):
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(
            f"{agente} (pensamento): {resposta}", [agente]
        )
    st.session_state.envolvidos_rodada_atual.add(agente)
    registrar_fala(agente, resposta, aprovada=True, privado=True)


def chunked(lista, tamanho):
    for i in range(0, len(lista), tamanho):
        yield lista[i : i + tamanho]


def indice_seguro(lista, valor, padrao=0):
    try:
        return lista.index(valor)
    except ValueError:
        return padrao


def iniciais(nome: str) -> str:
    return "".join([p[0].upper() for p in nome.replace("_", " ").split()][:2]) or "?"


# ----------------------------------------------------------------------------
# AÇÕES (equivalentes às opções do menu do main.py original)
# ----------------------------------------------------------------------------
def acao_iniciar_rodada():
    st.session_state.rodada_ativa = True
    st.session_state.envolvidos_rodada_atual = set()
    GerenciadorMemoriaRPG.salvar_log_rodada_atual(
        "--- ÍNICIO DA RODADA ---", carregar_agentes()
    )
    st.session_state.mensagem_info = "🟢 Rodada iniciada."


def acao_finalizar_rodada():
    if not st.session_state.rodada_ativa:
        st.session_state.mensagem_info = "⚠️ Inicie a rodada antes de finalizar."
        return

    alvos = (
        list(st.session_state.envolvidos_rodada_atual)
        if st.session_state.envolvidos_rodada_atual
        else carregar_agentes()
    )
    GerenciadorMemoriaRPG.salvar_log_rodada_atual("--- FIM DA RODADA ---", alvos)
    GerenciadorMemoriaRPG.finalizar_rodada(alvos)

    nao_envolvidos = [ag for ag in carregar_agentes() if ag not in alvos]
    if nao_envolvidos:
        GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

    st.session_state.rodada_ativa = False
    st.session_state.historico = []
    st.session_state.ultima_fala = {}
    st.session_state.mensagem_info = "⏹️ Rodada finalizada e memória consolidada."


def acao_falar_com_todos(presentes, comando_mestre, caminho_imagem):
    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
    st.session_state.historico.append(log_mestre)
    for p in presentes:
        st.session_state.envolvidos_rodada_atual.add(p)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, presentes)

    for ag in presentes:
        if obter_status_jogador(ag) != "vivo":
            continue
        resposta = gerar_resposta_agente(
            ag,
            f"O mestre disse a todos: '{comando_mestre}'. Dê sua reação no formato com tags [pensamento], [fala], [acao] ou [duvida].",
            st.session_state.historico,
            caminho_imagem=caminho_imagem,
        )
        tags = extrair_tags_resposta(resposta)
        publico = formatar_conteudo_publico(tags)

        # 1. Salva pensamento na memória privada do personagem
        if tags.get("pensamento"):
            salvar_pensamento_privado(
                ag, f"[pensamento]{tags['pensamento']}[/pensamento]"
            )

        # 2. Se houver fala ou ação pública, espelha para o chat e para os presentes
        if publico:
            log_ag = f"{ag}: {publico}"
            st.session_state.historico.append(log_ag)
            registrar_fala(ag, publico, aprovada=True, privado=False)
            if st.session_state.rodada_ativa:
                GerenciadorMemoriaRPG.salvar_resposta_agente(ag, resposta, presentes)
        elif not tags.get("pensamento"):
            log_ag = f"{ag}: {resposta}"
            st.session_state.historico.append(log_ag)
            registrar_fala(ag, resposta, aprovada=True, privado=False)
            if st.session_state.rodada_ativa:
                GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_ag, presentes)


def acao_falar_direcionado(presentes, is_privado, comando_mestre, caminho_imagem):
    agentes_alvo_log = presentes if is_privado else carregar_agentes()
    for p in agentes_alvo_log:
        st.session_state.envolvidos_rodada_atual.add(p)

    log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
    st.session_state.historico.append(log_mestre)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)

    alvo_principal = presentes[0]
    status_alvo = obter_status_jogador(alvo_principal)
    if status_alvo != "vivo":
        st.session_state.mensagem_info = f"⚠️ Não é possível falar com {alvo_principal}. Status: [{status_alvo.upper()}]."
        return

    resposta = gerar_resposta_agente(
        alvo_principal,
        f"O mestre direcionou a você: '{comando_mestre}'. Responda usando as tags [pensamento], [fala], [acao] ou [duvida].",
        st.session_state.historico,
        caminho_imagem=caminho_imagem,
    )

    tags = extrair_tags_resposta(resposta)
    publico = formatar_conteudo_publico(tags)

    # 1. Se houver pensamento, grava imediatamente na memória privada do personagem
    if tags.get("pensamento"):
        salvar_pensamento_privado(
            alvo_principal, f"[pensamento]{tags['pensamento']}[/pensamento]"
        )

    # 2. Se for apenas pensamento, encerra o turno
    if apenas_pensamento(tags):
        st.session_state.mensagem_info = (
            f"💭 {alvo_principal} teve um pensamento privado — não realizou ações públicas neste turno."
        )
        return

    # 3. Se houver conteúdo público (fala/ação/dúvida), envia para aprovação do Mestre
    conteudo_para_aprovar = publico or resposta
    st.session_state.pending_principal = {
        "alvo": alvo_principal,
        "resposta_completa": resposta,
        "conteudo_publico": conteudo_para_aprovar,
        "tags": tags,
        "presentes": presentes,
        "agentes_alvo_log": agentes_alvo_log,
    }
    registrar_fala(alvo_principal, conteudo_para_aprovar, aprovada=False, privado=False)


def aprovar_principal():
    p = st.session_state.pending_principal
    tags = p.get("tags") or extrair_tags_resposta(p["resposta_completa"])
    publico = p["conteudo_publico"]

    log_acao = f"{p['alvo']}: {publico}"
    st.session_state.historico.append(log_acao)
    registrar_fala(p["alvo"], publico, aprovada=True, privado=False)

    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            p["alvo"], p["resposta_completa"], p["agentes_alvo_log"]
        )

    outros_presentes = [x for x in p["presentes"] if x != p["alvo"]]

    if tem_duvida(tags) and outros_presentes:
        candidatos = [x for x in outros_presentes if obter_status_jogador(x) == "vivo"]
        st.session_state.aguardando_redirect = {
            "candidatos": candidatos,
            "alvo_principal": p["alvo"],
            "resposta_pergunta": tags.get("duvida") or publico,
            "agentes_alvo_log": p["agentes_alvo_log"],
        }
    elif tem_acao(tags):
        st.session_state.mensagem_info = (
            f"✅ Ação de {p['alvo']} resolvida. Nenhuma reação automática dos demais."
        )
    elif outros_presentes:
        for ou in outros_presentes:
            if obter_status_jogador(ou) != "vivo":
                continue
            resp_outro = gerar_resposta_agente(
                ou,
                f"O jogador {p['alvo']} acabou de dizer/fazer: '{publico}'. Você concorda, opina, faz ressalva "
                f"ou apenas pensa a respeito? Use as tags [pensamento], [fala], [acao] ou [duvida]. Seja breve.",
                st.session_state.historico,
                caminho_imagem=None,
            )
            tags_outro = extrair_tags_resposta(resp_outro)
            publico_outro = formatar_conteudo_publico(tags_outro)

            if tags_outro.get("pensamento"):
                salvar_pensamento_privado(
                    ou, f"[pensamento]{tags_outro['pensamento']}[/pensamento]"
                )

            if publico_outro:
                log_outro = f"{ou} (opinião): {publico_outro}"
                st.session_state.historico.append(log_outro)
                registrar_fala(ou, publico_outro, aprovada=True, privado=False)
                if st.session_state.rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(
                        ou, resp_outro, p["agentes_alvo_log"]
                    )

    st.session_state.pending_principal = None


def gerar_redirects(destinos):
    ar = st.session_state.aguardando_redirect
    pendentes = []
    for destino in destinos:
        resp = gerar_resposta_agente(
            destino,
            f"{ar['alvo_principal']} perguntou diretamente a você: '{ar['resposta_pergunta']}'. "
            f"Responda diretamente usando as tags [pensamento], [fala], [acao] ou [duvida].",
            st.session_state.historico,
            caminho_imagem=None,
        )
        tags = extrair_tags_resposta(resp)
        publico = formatar_conteudo_publico(tags)

        if tags.get("pensamento"):
            salvar_pensamento_privado(
                destino, f"[pensamento]{tags['pensamento']}[/pensamento]"
            )

        if apenas_pensamento(tags):
            continue

        conteudo_para_aprovar = publico or resp
        pendentes.append(
            {
                "destino": destino,
                "resposta_completa": resp,
                "conteudo_publico": conteudo_para_aprovar,
                "tags": tags,
                "alvo_principal": ar["alvo_principal"],
                "agentes_alvo_log": ar["agentes_alvo_log"],
            }
        )
        registrar_fala(destino, conteudo_para_aprovar, aprovada=False, privado=False)

    st.session_state.pending_redirects = pendentes
    st.session_state.aguardando_redirect = None
    if not pendentes and destinos:
        st.session_state.mensagem_info = "💭 A resposta foi um pensamento privado — não há nada para aprovar/espelhar."


def aprovar_redirect(indice):
    r = st.session_state.pending_redirects.pop(indice)
    log_redirect = f"{r['destino']} (resposta a {r['alvo_principal']}): {r['conteudo_publico']}"
    st.session_state.historico.append(log_redirect)
    registrar_fala(r["destino"], r["conteudo_publico"], aprovada=True, privado=False)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_resposta_agente(
            r["destino"], r["resposta_completa"], r["agentes_alvo_log"]
        )


def descartar_redirect(indice):
    r = st.session_state.pending_redirects.pop(indice)
    limpar_fala(r["destino"])


# ----------------------------------------------------------------------------
# BARRA LATERAL
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Mesa")

    if st.session_state.rodada_ativa:
        st.success("Rodada em andamento")
        if st.button("⏹️ Finalizar Rodada", use_container_width=True):
            acao_finalizar_rodada()
            st.rerun()
    else:
        st.info("Nenhuma rodada ativa")
        if st.button("▶️ Iniciar Rodada", use_container_width=True):
            acao_iniciar_rodada()
            st.rerun()

    st.divider()

    arquivos_regras_sidebar = listar_arquivos_regras()
    regra_ativa_sidebar = obter_regra_ativa()
    st.caption("📖 Regras em uso agora")
    troca_rapida = st.selectbox(
        "Trocar rapidamente",
        arquivos_regras_sidebar,
        index=indice_seguro(arquivos_regras_sidebar, regra_ativa_sidebar),
        key="troca_rapida_regras",
        label_visibility="collapsed",
    )
    if troca_rapida != regra_ativa_sidebar:
        definir_regra_ativa(troca_rapida)
        st.session_state.mensagem_info = (
            f"⭐ '{troca_rapida}' passou a ser o conjunto ativo."
        )
        st.rerun()

    if st.button(
        "✏️ Gerenciar / Criar Regras (arquivos/regras/)",
        use_container_width=True,
    ):
        st.session_state.editando_regras = True
        st.session_state.editando_ficha = None
        st.session_state.vendo_memoria = None
        st.session_state.trocando_avatar = None
        st.rerun()

    st.divider()
    st.subheader("➕ Adicionar Jogador")
    with st.form("form_novo_jogador", clear_on_submit=True):
        novo_nome = st.text_input("Nome (sem espaços, ex: JogadorD)")
        enviado = st.form_submit_button("Adicionar")
        if enviado:
            if adicionar_agente(novo_nome):
                obter_pasta_agente(novo_nome.strip())
                st.session_state.mensagem_info = (
                    f"✅ {novo_nome.strip()} adicionado à mesa."
                )
            else:
                st.session_state.mensagem_info = "⚠️ Nome inválido ou já existente."
            st.rerun()

    st.caption(
        "Novos jogadores entram automaticamente na fila de cards abaixo — "
        "não é preciso reiniciar o app."
    )

if st.session_state.mensagem_info:
    st.info(st.session_state.mensagem_info)
    st.session_state.mensagem_info = None


# ----------------------------------------------------------------------------
# GERENCIAMENTO DE REGRAS (múltiplos conjuntos em arquivos/regras/, um ativo por vez)
# ----------------------------------------------------------------------------
if st.session_state.editando_regras:
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
            st.session_state.mensagem_info = (
                "⚠️ Não foi possível excluir esse conjunto."
            )
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
                st.session_state.mensagem_info = f"✅ '{novo_arquivo}' criado (vazio) — selecione-o acima para escrever o conteúdo."
            else:
                st.session_state.mensagem_info = (
                    "⚠️ Nome inválido ou já existe um arquivo com esse nome."
                )
            st.rerun()

    if st.button("Fechar", key="fechar_regras"):
        st.session_state.editando_regras = False
        st.rerun()
    st.divider()


# ----------------------------------------------------------------------------
# TÍTULO E CARDS DE JOGADORES
# ----------------------------------------------------------------------------
st.title("🎲 Mesa de RPG — Painel do Mestre")

agentes = carregar_agentes()

if not agentes:
    st.warning("Nenhum jogador cadastrado. Adicione um jogador na barra lateral.")

st.subheader("👥 Jogadores")

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

for grupo in chunked(agentes, 4):
    cols = st.columns(len(grupo))
    for col, nome in zip(cols, grupo):
        with col:
            with st.container(border=True):
                status = obter_status_jogador(nome)
                cor = "#3d7a4f" if status == "vivo" else "#7a3d3d"
                foto = caminho_avatar(nome)
                if foto:
                    st.image(foto, width=64)
                else:
                    st.markdown(
                        CSS_AVATAR.format(cor=cor, iniciais=iniciais(nome)),
                        unsafe_allow_html=True,
                    )
                st.markdown(f"**{nome}**")
                st.caption(f"status: {status}")

                b1, b2, b3 = st.columns(3)
                if b1.button(
                    "✏️",
                    key=f"btn_ficha_{nome}",
                    use_container_width=True,
                    help="Editar ficha",
                ):
                    st.session_state.editando_ficha = nome
                    st.session_state.vendo_memoria = None
                    st.session_state.editando_regras = False
                    st.session_state.trocando_avatar = None
                    st.rerun()
                if b2.button(
                    "📜",
                    key=f"btn_mem_{nome}",
                    use_container_width=True,
                    help="Ver memória",
                ):
                    st.session_state.vendo_memoria = nome
                    st.session_state.editando_ficha = None
                    st.session_state.editando_regras = False
                    st.session_state.trocando_avatar = None
                    st.rerun()
                if b3.button(
                    "🖼️",
                    key=f"btn_avatar_{nome}",
                    use_container_width=True,
                    help="Trocar foto",
                ):
                    st.session_state.trocando_avatar = nome
                    st.session_state.editando_ficha = None
                    st.session_state.vendo_memoria = None
                    st.session_state.editando_regras = False
                    st.rerun()

                novo_status = st.selectbox(
                    "Status",
                    ["vivo", "morto", "inconsciente"],
                    index=(
                        ["vivo", "morto", "inconsciente"].index(status)
                        if status in ["vivo", "morto", "inconsciente"]
                        else 0
                    ),
                    key=f"status_{nome}",
                    label_visibility="collapsed",
                )
                if novo_status != status:
                    definir_status_jogador(nome, novo_status)
                    st.rerun()

                fala = st.session_state.ultima_fala.get(nome)
                if fala:
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
                    elif not aprovada:
                        st.caption("⏳ aguardando aprovação do mestre")

st.divider()

# ----------------------------------------------------------------------------
# PAINEL DE TROCA DE FOTO
# ----------------------------------------------------------------------------
if st.session_state.trocando_avatar:
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

# ----------------------------------------------------------------------------
# PAINEL DE EDIÇÃO DE FICHA
# ----------------------------------------------------------------------------
if st.session_state.editando_ficha:
    nome = st.session_state.editando_ficha
    st.subheader(f"✏️ Editando ficha de {nome}")
    conteudo_ficha = st.text_area(
        "Conteúdo da ficha",
        value=carregar_ficha(nome),
        height=250,
        key=f"txt_ficha_{nome}",
    )
    c1, c2 = st.columns([1, 1])
    if c1.button("💾 Salvar ficha", type="primary", key=f"salvar_ficha_{nome}"):
        salvar_ficha(nome, conteudo_ficha)
        st.session_state.editando_ficha = None
        st.session_state.mensagem_info = f"✅ Ficha de {nome} salva."
        st.rerun()
    if c2.button("Cancelar", key=f"cancelar_ficha_{nome}"):
        st.session_state.editando_ficha = None
        st.rerun()
    st.divider()


# ----------------------------------------------------------------------------
# PAINEL DE VISUALIZAÇÃO DE MEMÓRIA (somente leitura)
# ----------------------------------------------------------------------------
if st.session_state.vendo_memoria:
    nome = st.session_state.vendo_memoria
    st.subheader(f"📜 Memória de {nome}")
    dados = obter_arquivos_memoria(nome)

    with st.expander("Rodada atual (em aberto)", expanded=True):
        st.text(dados["rodada_atual"] or "Nenhuma rodada em aberto para este jogador.")

    if dados["rodadas"]:
        with st.expander(f"Rodadas fechadas ({len(dados['rodadas'])})"):
            for nome_arq, conteudo in dados["rodadas"]:
                st.markdown(f"**{nome_arq}**")
                st.text(conteudo)
                st.markdown("---")

    if dados["cenas"]:
        with st.expander(f"Cenas compiladas ({len(dados['cenas'])})"):
            for nome_arq, conteudo in dados["cenas"]:
                st.markdown(f"**{nome_arq}**")
                st.text(conteudo)
                st.markdown("---")

    with st.expander("Histórico permanente (mesa.txt)"):
        st.text(dados["mesa"] or "Ainda não há capítulos compilados na mesa.txt.")

    if st.button("Fechar visualização", key=f"fechar_mem_{nome}"):
        st.session_state.vendo_memoria = None
        st.rerun()
    st.divider()


# ----------------------------------------------------------------------------
# PAINEL DE AÇÃO DO MESTRE
# ----------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------
# CONFIRMAÇÃO DA RESPOSTA PRINCIPAL (falar direcionado)
# ----------------------------------------------------------------------------
if st.session_state.pending_principal:
    p = st.session_state.pending_principal
    tags = p.get("tags") or extrair_tags_resposta(p.get("resposta_completa", ""))
    st.subheader(f"🤖 Retorno de {p['alvo']}")

    if tags.get("pensamento"):
        st.info(
            f"💭 **Pensamento Íntimo (privado do personagem):**\n\n_{tags['pensamento']}_"
        )
    if tags.get("fala"):
        st.markdown(f"🗣️ **Fala:** *\"{tags['fala']}\"*")
    if tags.get("acao"):
        st.markdown(f"⚔️ **Ação:** *{tags['acao']}*")
    if tags.get("duvida"):
        st.markdown(f"❓ **Dúvida:** *{tags['duvida']}*")
    if not (tags.get("fala") or tags.get("acao") or tags.get("duvida")):
        st.markdown(f"> {p.get('conteudo_publico', '')}")

    c1, c2 = st.columns(2)
    if c1.button("✅ Aprovar / Espelhar", type="primary", key="aprovar_principal"):
        aprovar_principal()
        st.rerun()
    if c2.button("❌ Descartar", key="descartar_principal"):
        limpar_fala(p["alvo"])
        st.session_state.pending_principal = None
        st.session_state.mensagem_info = (
            "❌ Mensagem descartada. Nada foi salvo na história."
        )
        st.rerun()
    st.divider()

# ----------------------------------------------------------------------------
# REDIRECIONAMENTO DE DÚVIDA
# ----------------------------------------------------------------------------
if st.session_state.aguardando_redirect:
    ar = st.session_state.aguardando_redirect
    st.subheader(f"❓ {ar['alvo_principal']} fez uma pergunta/dúvida")
    st.markdown(f"> {ar['resposta_pergunta']}")

    if not ar["candidatos"]:
        st.warning("Nenhum outro jogador presente está disponível para responder.")
        if st.button("Ok, seguir sem redirecionar"):
            st.session_state.aguardando_redirect = None
            st.rerun()
    else:
        destinos = st.multiselect(
            "Para quem deseja redirecionar essa dúvida?", ar["candidatos"]
        )
        c1, c2 = st.columns(2)
        if c1.button("Gerar resposta(s)", type="primary", disabled=not destinos):
            gerar_redirects(destinos)
            st.rerun()
        if c2.button("Não redirecionar"):
            st.session_state.aguardando_redirect = None
            st.rerun()
    st.divider()

# ----------------------------------------------------------------------------
# CONFIRMAÇÃO DAS RESPOSTAS REDIRECIONADAS
# ----------------------------------------------------------------------------
if st.session_state.pending_redirects:
    st.subheader("🤖 Respostas às dúvidas redirecionadas")
    for i, r in enumerate(list(st.session_state.pending_redirects)):
        tags_r = r.get("tags") or extrair_tags_resposta(r.get("resposta_completa", ""))
        st.markdown(f"**{r['destino']}** (resposta a {r['alvo_principal']}):")
        if tags_r.get("pensamento"):
            st.info(f"💭 **Pensamento Íntimo:** _{tags_r['pensamento']}_")
        if tags_r.get("fala"):
            st.markdown(f"🗣️ **Fala:** *\"{tags_r['fala']}\"*")
        if tags_r.get("acao"):
            st.markdown(f"⚔️ **Ação:** *{tags_r['acao']}*")
        if tags_r.get("duvida"):
            st.markdown(f"❓ **Dúvida:** *{tags_r['duvida']}*")
        if not (tags_r.get("fala") or tags_r.get("acao") or tags_r.get("duvida")):
            st.markdown(f"> {r.get('conteudo_publico', '')}")
        c1, c2 = st.columns(2)
        if c1.button("✅ Aprovar", key=f"aprovar_redirect_{i}"):
            aprovar_redirect(i)
            st.rerun()
        if c2.button("❌ Descartar", key=f"descartar_redirect_{i}"):
            descartar_redirect(i)
            st.rerun()
        st.markdown("---")


# ----------------------------------------------------------------------------
# HISTÓRICO DA CENA/RODADA ATUAL
# ----------------------------------------------------------------------------
st.subheader("🗒️ Histórico da cena atual")
if not st.session_state.historico:
    st.caption("Nenhum evento ainda nesta rodada.")
else:
    for linha in st.session_state.historico:
        if ":" in linha:
            autor, resto = linha.split(":", 1)
        else:
            autor, resto = "Mestre", linha
        with st.chat_message(
            "assistant" if autor.strip() not in ("Mestre",) else "user"
        ):
            st.markdown(f"**{autor.strip()}**: {resto.strip()}")
