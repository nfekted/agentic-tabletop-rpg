# Configuração global: modelos de linguagem e gerenciamento de jogadores
# persistidos centralizadamente em arquivos/jogadores.json.

import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

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

# --- MODELOS DE LINGUAGEM ---
llm_historiador = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
llm_jogadores = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=1.6)

# --- ARMAZENAMENTO CENTRALIZADO DE JOGADORES ---
_PASTA_ARQUIVOS = os.path.join(_PASTA_DESTE_ARQUIVO, "arquivos")
_CAMINHO_JOGADORES = os.path.join(_PASTA_ARQUIVOS, "jogadores.json")


def carregar_agentes() -> list:
    """Lê e retorna a lista de nomes de agentes em arquivos/jogadores.json."""
    if not os.path.exists(_CAMINHO_JOGADORES):
        os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
        with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        return []

    try:
        with open(_CAMINHO_JOGADORES, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                return [str(a).strip() for a in dados if str(a).strip()]
    except Exception:
        pass
    return []


def adicionar_agente(nome: str) -> bool:
    """Adiciona um novo nome à lista centralizada e inicializa ficha e memória."""
    nome = nome.strip()
    if not nome or not nome.isidentifier():
        return False

    agentes_atuais = carregar_agentes()
    if nome in agentes_atuais:
        return False

    nova_lista = agentes_atuais + [nome]
    os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
    with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
        json.dump(nova_lista, f, indent=2, ensure_ascii=False)

    # 1. Garante que a pasta de memória do agente exista
    pasta_memoria = os.path.join(_PASTA_ARQUIVOS, f"memoria_{nome}")
    os.makedirs(pasta_memoria, exist_ok=True)

    # 2. Garante que a ficha inicial do agente exista
    pasta_fichas = os.path.join(_PASTA_ARQUIVOS, "fichas")
    os.makedirs(pasta_fichas, exist_ok=True)
    caminho_ficha = os.path.join(pasta_fichas, f"{nome.lower()}.txt")

    if not os.path.exists(caminho_ficha):
        caminho_template = os.path.join(pasta_fichas, "default.txt")
        template = ""
        if os.path.exists(caminho_template):
            with open(caminho_template, "r", encoding="utf-8") as f:
                template = f.read()
            template = template.replace("[Nome do Personagem]", nome)
        else:
            template = f"# FICHA DE PERSONAGEM: {nome}\n"

        conteudo_ficha = f"status: vivo\n\n{template}"
        with open(caminho_ficha, "w", encoding="utf-8") as f:
            f.write(conteudo_ficha)

    return True


def remover_agente(nome: str) -> bool:
    """Remove um agente da lista em arquivos/jogadores.json."""
    nome = nome.strip()
    agentes_atuais = carregar_agentes()
    if nome not in agentes_atuais:
        return False

    nova_lista = [a for a in agentes_atuais if a != nome]
    with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
        json.dump(nova_lista, f, indent=2, ensure_ascii=False)
    return True


def __getattr__(name: str):
    """Permite que 'from config import AGENTES' ou 'config.AGENTES' funcione dinamicamente."""
    if name == "AGENTES":
        return carregar_agentes()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
