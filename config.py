import json
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama

_PASTA_DESTE_ARQUIVO = os.path.dirname(os.path.abspath(__file__))
_PASTA_ARQUIVOS = os.path.join(_PASTA_DESTE_ARQUIVO, "arquivos")
_CAMINHO_CONFIG = os.path.join(_PASTA_ARQUIVOS, "config.json")
_CAMINHO_JOGADORES = os.path.join(_PASTA_ARQUIVOS, "jogadores.json")

PROVEDORES = ["Gemini 3.5-flash", "GPT-luna", "Ollama local", "Omniroute local"]

CONFIG_PADRAO = {
    "provedor": "Omniroute local",
    "api_key": "",
    "base_url": "http://localhost:8000/v1",
}


def carregar_configuracao() -> dict:
    os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
    if not os.path.exists(_CAMINHO_CONFIG):
        salvar_configuracao(CONFIG_PADRAO)
        return CONFIG_PADRAO
    try:
        with open(_CAMINHO_CONFIG, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return {**CONFIG_PADRAO, **dados}
    except Exception:
        return CONFIG_PADRAO


def salvar_configuracao(dados: dict):
    os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
    with open(_CAMINHO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def obter_llm(temperature: float = 0.8):
    cfg = carregar_configuracao()
    provedor = cfg.get("provedor")
    api_key = cfg.get("api_key")
    base_url = cfg.get("base_url")

    # Limita a temperatura em 1.0 para evitarem erros de API
    temp_normalizada = min(temperature, 1.0)

    if provedor == "Gemini 3.5-flash":
        return ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=api_key or os.getenv("GEMINI_API_KEY"),
            temperature=temp_normalizada,
        )
    elif provedor == "GPT-luna":
        return ChatOpenAI(
            model="gpt-luna",
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=temp_normalizada,
        )
    elif provedor == "Ollama local":
        return Ollama(
            model="llama3",
            base_url=base_url or "http://localhost:11434",
            temperature=temp_normalizada,
        )
    elif provedor == "Omniroute local":
        return ChatOpenAI(
            model="omniroute-local",
            api_key=api_key or "local-key",
            base_url=base_url or "http://localhost:8000/v1",
            temperature=temp_normalizada,
        )
    else:
        raise ValueError(f"Provedor desconhecido: {provedor}")


# --- ARMAZENAMENTO CENTRALIZADO DE JOGADORES ---
def carregar_agentes() -> list:
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

    pasta_memoria = os.path.join(_PASTA_ARQUIVOS, f"memoria_{nome}")
    os.makedirs(pasta_memoria, exist_ok=True)
    pasta_fichas = os.path.join(_PASTA_ARQUIVOS, "fichas")
    os.makedirs(pasta_fichas, exist_ok=True)
    caminho_ficha = os.path.join(pasta_fichas, f"{nome.lower()}.txt")

    if not os.path.exists(caminho_ficha):
        caminho_template = os.path.join(pasta_fichas, "default.txt")
        template = ""
        if os.path.exists(caminho_template):
            with open(caminho_template, "r", encoding="utf-8") as f:
                template = f.read().replace("[Nome do Personagem]", nome)
        else:
            template = f"# FICHA DE PERSONAGEM: {nome}\n"
        with open(caminho_ficha, "w", encoding="utf-8") as f:
            f.write(f"status: vivo\n\n{template}")
    return True


def remover_agente(nome: str) -> bool:
    nome = nome.strip()
    agentes_atuais = carregar_agentes()
    if nome not in agentes_atuais:
        return False
    nova_lista = [a for a in agentes_atuais if a != nome]
    with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
        json.dump(nova_lista, f, indent=2, ensure_ascii=False)
    return True


def __getattr__(name: str):
    if name == "AGENTES":
        return carregar_agentes()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
