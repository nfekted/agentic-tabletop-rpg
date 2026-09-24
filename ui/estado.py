# Inicialização do st.session_state e pequenas funções auxiliares puras
# (sem regra de negócio — só utilidades usadas em vários painéis)
import streamlit as st


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
        "current_view": "mesa",
        "token_categoria": "inimigo",
        "token_selecionado": None,
    }
    for chave, valor in padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


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
