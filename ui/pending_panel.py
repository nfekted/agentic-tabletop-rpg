# Painéis de confirmação da resposta principal, redirecionamento de dúvida
# e confirmação das respostas redirecionadas.
import streamlit as st

from tags import extrair_tags_resposta

from ui.fala import limpar_fala
from ui.acoes import aprovar_principal, gerar_redirects, aprovar_redirect, descartar_redirect


def renderizar_pending_principal():
    if not st.session_state.pending_principal:
        return

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


def renderizar_aguardando_redirect():
    if not st.session_state.aguardando_redirect:
        return

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


def renderizar_pending_redirects():
    if not st.session_state.pending_redirects:
        return

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


def renderizar_pending_panels():
    renderizar_pending_principal()
    renderizar_aguardando_redirect()
    renderizar_pending_redirects()
