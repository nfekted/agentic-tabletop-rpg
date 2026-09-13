# Configuração global: agentes (jogadores), modelos de linguagem e utilitário
# para adicionar novos jogadores dinamicamente (persistindo neste arquivo).

import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Aponta explicitamente para o .env que fica na MESMA pasta deste arquivo,
# em vez de depender do diretório de onde o comando "streamlit run" foi
# executado (load_dotenv() sozinho só olha o cwd do terminal, o que causava
# "API key required" mesmo com o .env preenchido).
_PASTA_DESTE_ARQUIVO = os.path.dirname(os.path.abspath(__file__))
_CAMINHO_ENV = os.path.join(_PASTA_DESTE_ARQUIVO, ".env")
load_dotenv(dotenv_path=_CAMINHO_ENV)

if not (os.getenv("GEMINI_API_KEY")):
    raise RuntimeError(
        "Nenhuma API key encontrada. Verifique se existe um arquivo '.env' em "
        f"'{_PASTA_DESTE_ARQUIVO}' contendo a linha:\n"
        'GEMINI_API_KEY="sua_chave_aqui"\n'
        "(sem aspas, sem espaços ao redor do '=')."
    )

# --- LISTA DE JOGADORES ---
# Pode ser editada manualmente aqui, ou através do botão "Adicionar Jogador"
# na tela do Streamlit (que reescreve esta lista automaticamente).
AGENTES = []

# --- MODELOS DE LINGUAGEM ---
llm_historiador = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
llm_jogadores = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=1.6)


_CAMINHO_CONFIG = os.path.abspath(__file__)


def carregar_agentes() -> list:
    # Relê este próprio arquivo do disco e retorna a lista AGENTES atual.
    global AGENTES
    with open(_CAMINHO_CONFIG, "r", encoding="utf-8") as f:
        conteudo = f.read()

    m = re.search(r"^AGENTES\s*=\s*(\[[^\]]*\])", conteudo, re.MULTILINE)
    if m:
        try:
            nova_lista = eval(m.group(1), {"__builtins__": {}})
            if isinstance(nova_lista, list):
                AGENTES = nova_lista
        except Exception:
            pass
    return AGENTES


def adicionar_agente(nome: str) -> bool:
    # Adiciona um novo nome à lista AGENTES e persiste no config.py.

    nome = nome.strip()
    if not nome or not nome.isidentifier():
        return False

    agentes_atuais = carregar_agentes()
    if nome in agentes_atuais:
        return False

    nova_lista = agentes_atuais + [nome]

    with open(_CAMINHO_CONFIG, "r", encoding="utf-8") as f:
        conteudo = f.read()

    lista_formatada = "[" + ", ".join(f'"{a}"' for a in nova_lista) + "]"
    conteudo_novo = re.sub(
        r"^AGENTES\s*=\s*\[[^\]]*\]",
        f"AGENTES = {lista_formatada}",
        conteudo,
        count=1,
        flags=re.MULTILINE,
    )

    with open(_CAMINHO_CONFIG, "w", encoding="utf-8") as f:
        f.write(conteudo_novo)

    global AGENTES
    AGENTES = nova_lista
    return True
