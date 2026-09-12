# Interface visual (Streamlit) para o Mestre conduzir a mesa de RPG,
# substituindo o menu de terminal do main.py original por botões/campos.

import streamlit as st

from config import carregar_agentes, adicionar_agente
from fichas import (
    carregar_regras,
    salvar_regras,
    carregar_ficha,
    salvar_ficha,
    obter_status_jogador,
    definir_status_jogador,
)
from imagens import salvar_imagem_upload, caminho_avatar, salvar_avatar_jogador, remover_avatar_jogador
from memoria import obter_pasta_agente, obter_arquivos_memoria, GerenciadorMemoriaRPG
from agentes import gerar_resposta_agente

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


def registrar_fala(agente: str, texto: str, aprovada: bool = True):
    #Guarda a última fala de um agente para exibir como balão junto ao seu
    #card. 'aprovada=False' marca uma resposta ainda não espelhada pelo mestre
    #(aparece com estilo tracejado até ser aprovada ou descartada).
    st.session_state.ultima_fala[agente] = {"texto": texto, "aprovada": aprovada}


def limpar_fala(agente: str):
    st.session_state.ultima_fala.pop(agente, None)


def chunked(lista, tamanho):
    for i in range(0, len(lista), tamanho):
        yield lista[i : i + tamanho]


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
            f"O mestre disse a todos: '{comando_mestre}'. Dê sua reação breve.",
            st.session_state.historico,
            caminho_imagem=caminho_imagem,
        )
        log_ag = f"{ag}: {resposta}"
        st.session_state.historico.append(log_ag)
        registrar_fala(ag, resposta, aprovada=True)
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
        st.session_state.mensagem_info = (
            f"⚠️ Não é possível falar com {alvo_principal}. Status: [{status_alvo.upper()}]."
        )
        return

    resposta = gerar_resposta_agente(
        alvo_principal,
        f"O mestre direcionou a você: '{comando_mestre}'. Responda usando [acao] para agir ou [duvida] para consultar outro jogador.",
        st.session_state.historico,
        caminho_imagem=caminho_imagem,
    )

    st.session_state.pending_principal = {
        "alvo": alvo_principal,
        "resposta": resposta,
        "presentes": presentes,
        "agentes_alvo_log": agentes_alvo_log,
    }
    registrar_fala(alvo_principal, resposta, aprovada=False)


def aprovar_principal():
    p = st.session_state.pending_principal
    log_acao = f"{p['alvo']}: {p['resposta']}"
    st.session_state.historico.append(log_acao)
    registrar_fala(p["alvo"], p["resposta"], aprovada=True)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_acao, p["agentes_alvo_log"])

    outros_presentes = [x for x in p["presentes"] if x != p["alvo"]]
    resposta_lower = p["resposta"].lower()
    tem_duvida = "[duvida]" in resposta_lower
    tem_acao = "[acao]" in resposta_lower

    if tem_duvida and outros_presentes:
        candidatos = [x for x in outros_presentes if obter_status_jogador(x) == "vivo"]
        st.session_state.aguardando_redirect = {
            "candidatos": candidatos,
            "alvo_principal": p["alvo"],
            "resposta_pergunta": p["resposta"],
            "agentes_alvo_log": p["agentes_alvo_log"],
        }
    elif tem_acao:
        st.session_state.mensagem_info = (
            f"✅ Ação de {p['alvo']} resolvida. Nenhuma reação automática dos demais."
        )
    elif outros_presentes:
        for ou in outros_presentes:
            if obter_status_jogador(ou) != "vivo":
                continue
            resp_outro = gerar_resposta_agente(
                ou,
                f"O jogador {p['alvo']} acabou de dizer/fazer: '{p['resposta']}'. Você concorda, opina ou faz ressalva? Seja breve.",
                st.session_state.historico,
                caminho_imagem=None,
            )
            log_outro = f"{ou} (opinião): {resp_outro}"
            st.session_state.historico.append(log_outro)
            registrar_fala(ou, resp_outro, aprovada=True)
            if st.session_state.rodada_ativa:
                GerenciadorMemoriaRPG.salvar_log_rodada_atual(
                    log_outro, p["agentes_alvo_log"]
                )

    st.session_state.pending_principal = None


def gerar_redirects(destinos):
    ar = st.session_state.aguardando_redirect
    pendentes = []
    for destino in destinos:
        resp = gerar_resposta_agente(
            destino,
            f"{ar['alvo_principal']} perguntou diretamente a você: '{ar['resposta_pergunta']}'. "
            f"Responda a pergunta dele(a) diretamente, sem apenas opinar sobre o assunto.",
            st.session_state.historico,
            caminho_imagem=None,
        )
        pendentes.append(
            {
                "destino": destino,
                "resposta": resp,
                "alvo_principal": ar["alvo_principal"],
                "agentes_alvo_log": ar["agentes_alvo_log"],
            }
        )
        registrar_fala(destino, resp, aprovada=False)
    st.session_state.pending_redirects = pendentes
    st.session_state.aguardando_redirect = None


def aprovar_redirect(indice):
    r = st.session_state.pending_redirects.pop(indice)
    log_redirect = f"{r['destino']} (resposta a {r['alvo_principal']}): {r['resposta']}"
    st.session_state.historico.append(log_redirect)
    registrar_fala(r["destino"], r["resposta"], aprovada=True)
    if st.session_state.rodada_ativa:
        GerenciadorMemoriaRPG.salvar_log_rodada_atual(
            log_redirect, r["agentes_alvo_log"]
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

    if st.button("📖 Editar Regras Gerais (regras_rpg.txt)", use_container_width=True):
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
                st.session_state.mensagem_info = f"✅ {novo_nome.strip()} adicionado à mesa."
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
# EDIÇÃO DE REGRAS
# ----------------------------------------------------------------------------
if st.session_state.editando_regras:
    st.subheader("📖 Editando regras_rpg.txt")
    conteudo_regras = st.text_area(
        "Regras gerais da mesa", value=carregar_regras(), height=250, key="txt_regras"
    )
    c1, c2 = st.columns([1, 1])
    if c1.button("💾 Salvar regras", type="primary"):
        salvar_regras(conteudo_regras)
        st.session_state.editando_regras = False
        st.session_state.mensagem_info = "✅ Regras salvas."
        st.rerun()
    if c2.button("Cancelar", key="cancelar_regras"):
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
<div style="text-align:center; font-size:16px; line-height:8px; color:{borda};">▲</div>
<div style="
    position:relative;
    background:{fundo};
    border:{estilo_borda} 1.5px {borda};
    border-radius:12px;
    padding:8px 10px;
    font-size:13px;
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
                if b1.button("✏️", key=f"btn_ficha_{nome}", use_container_width=True, help="Editar ficha"):
                    st.session_state.editando_ficha = nome
                    st.session_state.vendo_memoria = None
                    st.session_state.editando_regras = False
                    st.session_state.trocando_avatar = None
                    st.rerun()
                if b2.button("📜", key=f"btn_mem_{nome}", use_container_width=True, help="Ver memória"):
                    st.session_state.vendo_memoria = nome
                    st.session_state.editando_ficha = None
                    st.session_state.editando_regras = False
                    st.session_state.trocando_avatar = None
                    st.rerun()
                if b3.button("🖼️", key=f"btn_avatar_{nome}", use_container_width=True, help="Trocar foto"):
                    st.session_state.trocando_avatar = nome
                    st.session_state.editando_ficha = None
                    st.session_state.vendo_memoria = None
                    st.session_state.editando_regras = False
                    st.rerun()

                novo_status = st.selectbox(
                    "Status",
                    ["vivo", "morto", "inconsciente"],
                    index=["vivo", "morto", "inconsciente"].index(status)
                    if status in ["vivo", "morto", "inconsciente"]
                    else 0,
                    key=f"status_{nome}",
                    label_visibility="collapsed",
                )
                if novo_status != status:
                    definir_status_jogador(nome, novo_status)
                    st.rerun()

                fala = st.session_state.ultima_fala.get(nome)
                if fala:
                    aprovada = fala["aprovada"]
                    st.markdown(
                        CSS_BALAO.format(
                            fundo="#f0f2f6" if aprovada else "#fff8e1",
                            borda="#c9c9c9" if aprovada else "#d9a441",
                            estilo_borda="solid" if aprovada else "dashed",
                            texto=fala["texto"],
                        ),
                        unsafe_allow_html=True,
                    )
                    if not aprovada:
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
        st.caption("Este jogador ainda não tem foto — está usando o quadrado com iniciais.")

    nova_foto = st.file_uploader(
        "Selecionar nova imagem", type=["png", "jpg", "jpeg", "webp"], key=f"upload_avatar_{nome}"
    )
    c1, c2, c3 = st.columns(3)
    if c1.button("💾 Salvar foto", type="primary", key=f"salvar_avatar_{nome}", disabled=nova_foto is None):
        salvar_avatar_jogador(nome, nova_foto)
        st.session_state.trocando_avatar = None
        st.session_state.mensagem_info = f"✅ Foto de {nome} atualizada."
        st.rerun()
    if c2.button("🗑️ Remover foto", key=f"remover_avatar_{nome}", disabled=atual is None):
        remover_avatar_jogador(nome)
        st.session_state.trocando_avatar = None
        st.session_state.mensagem_info = f"🗑️ Foto de {nome} removida — voltou ao quadrado com iniciais."
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
        "Conteúdo da ficha", value=carregar_ficha(nome), height=250, key=f"txt_ficha_{nome}"
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

comando_mestre = st.text_area("Sua mensagem/orientação", key="txt_comando_mestre")
imagem_upload = st.file_uploader(
    "Anexar imagem (opcional)", type=["png", "jpg", "jpeg", "webp"]
)

pode_enviar = bool(comando_mestre.strip()) and bool(selecionados)
if st.button("📨 Enviar", type="primary", disabled=not pode_enviar):
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
    st.subheader(f"🤖 Retorno de {p['alvo']}")
    st.markdown(f"> {p['resposta']}")
    c1, c2 = st.columns(2)
    if c1.button("✅ Aprovar / Espelhar", type="primary", key="aprovar_principal"):
        aprovar_principal()
        st.rerun()
    if c2.button("❌ Descartar", key="descartar_principal"):
        limpar_fala(p["alvo"])
        st.session_state.pending_principal = None
        st.session_state.mensagem_info = "❌ Mensagem descartada. Nada foi salvo na história."
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
        st.markdown(f"**{r['destino']}** (resposta a {r['alvo_principal']}):")
        st.markdown(f"> {r['resposta']}")
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
        with st.chat_message("assistant" if autor.strip() not in ("Mestre",) else "user"):
            st.markdown(f"**{autor.strip()}**: {resto.strip()}")