import json
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from rpg.fichas import inicializar_ficha_agente, salvar_json
from rpg.paths import ARQUIVOS

_CAMINHO_CONFIG = os.path.join(ARQUIVOS, "config.json")
_CAMINHO_JOGADORES = os.path.join(ARQUIVOS, "jogadores.json")

# tipo de API (qual cliente usar); o modelo é digitado pelo usuário, como na documentação do provedor
TIPOS_API = {"gemini": "Google Gemini", "openai": "OpenAI-compatível", "local": "Local (Ollama, Omniroute...)"}

CONFIG_PADRAO = {
    "tipo_api": "local",
    "modelo": "omniroute-local",
    "api_key": "",
    "base_url": "http://localhost:8000/v1",
    "limite_contexto_tokens": 0,  # 0 = controle de contexto desligado
    "gatilho_compressao_pct": 85,
    "alvo_reducao_pct": 50,  # % que será cortado do mesa.txt na compressão
    "limite_rpm": 0,  # limites do provedor (0 = sem controle)
    "limite_tpm": 0,
    "limite_rpd": 0,
}


def _migrar(dados: dict) -> dict:
    # configs antigas guardavam um nome de provedor fixo ("GPT-luna", "Ollama local"...)
    antigo = dados.pop("provedor", None)
    if antigo and "tipo_api" not in dados:
        tipo, modelo = {
            "gemini-3.5-flash-lite": ("gemini", "gemini-3.5-flash-lite"),
            "GPT-luna": ("openai", "gpt-luna"),
            "Ollama local": ("local", "llama3"),
        }.get(antigo, ("local", "omniroute-local"))
        dados["tipo_api"], dados["modelo"] = tipo, modelo
        url = (dados.get("base_url") or "").rstrip("/")
        if antigo == "Ollama local":  # o Ollama fala o protocolo OpenAI em /v1
            dados["base_url"] = (url or "http://localhost:11434") + ("" if url.endswith("/v1") else "/v1")
    return dados


def identidade_llm() -> str:
    # muda quando troca o tipo ou o modelo (as métricas de tokens são recalibradas)
    cfg = carregar_configuracao()
    return f"{cfg.get('tipo_api')}:{cfg.get('modelo')}"


def carregar_configuracao() -> dict:
    os.makedirs(ARQUIVOS, exist_ok=True)
    if not os.path.exists(_CAMINHO_CONFIG):
        salvar_configuracao(CONFIG_PADRAO)
        return CONFIG_PADRAO
    try:
        with open(_CAMINHO_CONFIG, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return {**CONFIG_PADRAO, **_migrar(dados)}
    except Exception:
        return CONFIG_PADRAO


def salvar_configuracao(dados: dict):
    salvar_json(_CAMINHO_CONFIG, dados)


def obter_llm(temperature: float = 0.8):
    cfg = carregar_configuracao()
    tipo = cfg.get("tipo_api")
    modelo = (cfg.get("modelo") or "").strip()
    api_key = cfg.get("api_key")
    base_url = (cfg.get("base_url") or "").strip()

    temp_normalizada = min(temperature, 1.0)

    if not modelo:
        raise ValueError("Informe o modelo nas configurações.")
    if tipo == "gemini":
        return ChatGoogleGenerativeAI(
            model=modelo,
            google_api_key=api_key or os.getenv("GEMINI_API_KEY"),
            temperature=temp_normalizada,
        )
    if tipo == "openai":
        return ChatOpenAI(
            model=modelo,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or None,
            temperature=temp_normalizada,
        )
    if tipo == "local":
        if not base_url:
            raise ValueError("Informe o endereço (base URL) do servidor local nas configurações.")
        return ChatOpenAI(
            model=modelo,
            api_key=api_key or "local-key",
            base_url=base_url,
            temperature=temp_normalizada,
        )
    raise ValueError(f"Tipo de API desconhecido: {tipo}")


def carregar_dados_jogadores() -> list:
    if not os.path.exists(_CAMINHO_JOGADORES):
        salvar_dados_jogadores([])
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
    salvar_json(_CAMINHO_JOGADORES, dados)


def carregar_agentes() -> list:
    dados = carregar_dados_jogadores()
    return [j["nome"] for j in dados if j.get("nome")]


def _achar_jogador(dados: list, nome: str) -> dict | None:
    return next((j for j in dados if j.get("nome", "").lower() == nome.lower()), None)


def obter_modificadores_jogador(nome: str) -> str:
    jogador = _achar_jogador(carregar_dados_jogadores(), nome)
    return jogador.get("modificadores", "") if jogador else ""


def salvar_modificadores_jogador(nome: str, modificadores: str):
    dados = carregar_dados_jogadores()
    jogador = _achar_jogador(dados, nome)
    if jogador:
        jogador["modificadores"] = modificadores.strip()
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

    os.makedirs(os.path.join(ARQUIVOS, f"memoria_{nome}"), exist_ok=True)
    inicializar_ficha_agente(nome)
    return True
