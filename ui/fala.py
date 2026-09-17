# Funções que controlam o "balão" de última fala exibido junto ao card de cada jogador
import streamlit as st


def registrar_fala(agente: str, texto: str, aprovada: bool = True, privado: bool = False):
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
