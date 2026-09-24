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
def carregar_dados_jogadores() -> list:
    if not os.path.exists(_CAMINHO_JOGADORES):
        os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
        with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        return []
    try:
        with open(_CAMINHO_JOGADORES, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                lista_normalizada = []
                precisa_salvar = False
                for item in dados:
                    if isinstance(item, dict) and "nome" in item:
                        lista_normalizada.append({
                            "nome": str(item["nome"]).strip(),
                            "modificadores": str(item.get("modificadores", "")).strip(),
                        })
                    elif isinstance(item, str) and item.strip():
                        lista_normalizada.append({
                            "nome": item.strip(),
                            "modificadores": "",
                        })
                        precisa_salvar = True
                if precisa_salvar:
                    salvar_dados_jogadores(lista_normalizada)
                return lista_normalizada
    except Exception:
        pass
    return []


def salvar_dados_jogadores(dados: list):
    os.makedirs(_PASTA_ARQUIVOS, exist_ok=True)
    with open(_CAMINHO_JOGADORES, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def carregar_agentes() -> list:
    dados = carregar_dados_jogadores()
    return [j["nome"] for j in dados if j.get("nome")]


def obter_modificadores_jogador(nome: str) -> str:
    dados = carregar_dados_jogadores()
    for j in dados:
        if j.get("nome", "").lower() == nome.lower():
            return j.get("modificadores", "")
    return ""


def salvar_modificadores_jogador(nome: str, modificadores: str):
    dados = carregar_dados_jogadores()
    for j in dados:
        if j.get("nome", "").lower() == nome.lower():
            j["modificadores"] = modificadores.strip()
            break
    salvar_dados_jogadores(dados)


def adicionar_agente(nome: str) -> bool:
    nome = nome.strip()
    if not nome or not nome.isidentifier():
        return False
    agentes_atuais = carregar_agentes()
    if nome.lower() in [a.lower() for a in agentes_atuais]:
        return False

    dados_atuais = carregar_dados_jogadores()
    dados_atuais.append({"nome": nome, "modificadores": ""})
    salvar_dados_jogadores(dados_atuais)

    pasta_memoria = os.path.join(_PASTA_ARQUIVOS, f"memoria_{nome}")
    os.makedirs(pasta_memoria, exist_ok=True)

    # Inicializa os 6 subarquivos modulares da ficha
    from fichas import inicializar_ficha_agente
    inicializar_ficha_agente(nome)
    return True


def remover_agente(nome: str) -> bool:
    nome = nome.strip()
    dados_atuais = carregar_dados_jogadores()
    nova_lista = [j for j in dados_atuais if j.get("nome", "").lower() != nome.lower()]
    if len(nova_lista) == len(dados_atuais):
        return False
    salvar_dados_jogadores(nova_lista)
    return True


def __getattr__(name: str):
    if name == "AGENTES":
        return carregar_agentes()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
