# Painel de ação do Mestre: escolha do tipo de fala, seleção de jogadores,
# cenas pré-salvas, mensagem/imagem e envio.
import streamlit as st

from cenas import deletar_cena, ler_cena, listar_cenas, nome_seguro, salvar_cena
from imagens import salvar_imagem_upload

from ui.acoes import acao_falar_com_todos, acao_falar_direcionado

OPCAO_NENHUMA = "— nenhuma —"
CHAVE_MENSAGEM = "comando_mestre"
CHAVE_CENA = "cena_selecionada"


# Callbacks (rodam ANTES do script reexecutar, por isso podem mexer
# no valor dos widgets sem dar erro)
def _carregar_cena_no_campo():
    nome = st.session_state.get(CHAVE_CENA)
    if nome and nome != OPCAO_NENHUMA:
        conteudo = ler_cena(nome)
        if conteudo:
            st.session_state[CHAVE_MENSAGEM] = conteudo
        else:
            # Se o arquivo não existir fisicamente (deletado na pasta),
            # reseta a seleção e avisa o usuário.
            st.session_state[CHAVE_CENA] = OPCAO_NENHUMA
            st.warning(
                f"A cena '{nome}' não foi encontrada no disco e foi removida da lista."
            )


def _resetar_selecao_cena():
    # Após enviar, volta o seletor para "nenhuma" para que dê para
    # escolher a mesma cena de novo depois.
    st.session_state[CHAVE_CENA] = OPCAO_NENHUMA


def excluir_cena():
    nome = st.session_state.get(CHAVE_CENA)
    if nome and nome != OPCAO_NENHUMA:
        deletar_cena(nome)
        st.session_state[CHAVE_CENA] = OPCAO_NENHUMA
        st.session_state[CHAVE_MENSAGEM] = ""


def renderizar_acao_mestre(agentes):
    col_acao, col_cenas = st.columns(2)

    # ---------------- 50% esquerda: Ação do Mestre ----------------
    with col_acao:
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
            selecionados = st.multiselect(
                "Selecione o(s) jogador(es) envolvidos", agentes
            )

    # ---------------- 50% direita: Cenas ----------------
    with col_cenas:
        st.subheader("🎭 Cenas")
        st.caption(
            "Defina cenas pré definidas, ou prompts pré salvos para agilizar a mesa"
        )
        aba_usar, aba_nova = st.tabs(["📂 Usar cena salva", "➕ Nova cena"])

        # A aba "Nova cena" é processada primeiro no código para que, ao salvar,
        # a lista da outra aba já apareça atualizada na mesma execução.
        with aba_nova:
            with st.form("form_nova_cena", clear_on_submit=True):
                nome_cena = st.text_input("Nome da cena")
                conteudo_cena = st.text_area("Conteúdo da cena", height=150)
                salvou = st.form_submit_button("💾 Salvar cena")

            if salvou:
                nome_limpo = nome_seguro(nome_cena)
                if not nome_limpo or not conteudo_cena.strip():
                    st.warning("Informe um nome e o conteúdo da cena.")
                else:
                    ja_existia = nome_limpo in listar_cenas()
                    salvar_cena(nome_limpo, conteudo_cena)
                    st.success(
                        f"Cena '{nome_limpo}' "
                        f"{'atualizada' if ja_existia else 'salva'}!"
                    )

        with aba_usar:
            cenas = listar_cenas()
            if cenas:
                cena_atual = st.selectbox(
                    "Selecione uma cena para carregar na mensagem",
                    [OPCAO_NENHUMA] + cenas,
                    key=CHAVE_CENA,
                    on_change=_carregar_cena_no_campo,
                )
                st.caption(
                    "Ao selecionar, o texto vai direto para o campo de mensagem abaixo."
                )

                # Botão de exclusão exibido apenas quando uma cena válida está selecionada
                if cena_atual and cena_atual != OPCAO_NENHUMA:
                    if st.button("🗑️ Excluir cena selecionada", type="secondary",on_click=excluir_cena):
                        st.rerun()
            else:
                st.info("Nenhuma cena salva ainda. Crie uma na aba 'Nova cena'.")

    # ---------------- 100%: mensagem / imagem / envio ----------------
    with st.form("form_envio_mestre", clear_on_submit=True):
        comando_mestre = st.text_area("Sua mensagem/orientação", key=CHAVE_MENSAGEM)
        imagem_upload = st.file_uploader(
            "Anexar imagem (opcional)", type=["png", "jpg", "jpeg", "webp"]
        )
        enviado = st.form_submit_button(
            "📨 Enviar",
            type="primary",
            disabled=not bool(selecionados),
            on_click=_resetar_selecao_cena,
        )

    if enviado:
        if not comando_mestre.strip():
            st.warning("Digite uma mensagem ou selecione uma cena antes de enviar.")
        else:
            caminho_imagem = (
                salvar_imagem_upload(imagem_upload) if imagem_upload else None
            )

            if tipo_acao == "Falar com Todos (Público)":
                acao_falar_com_todos(selecionados, comando_mestre, caminho_imagem)
            elif tipo_acao == "Falar com Jogador(es) Específico(s) [Cena Pública]":
                acao_falar_direcionado(
                    selecionados, False, comando_mestre, caminho_imagem
                )
            else:
                acao_falar_direcionado(
                    selecionados, True, comando_mestre, caminho_imagem
                )

            st.rerun()

    st.divider()
