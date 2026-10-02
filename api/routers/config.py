from fastapi import APIRouter
from pydantic import BaseModel

from rpg.config import PROVEDORES, carregar_configuracao, salvar_configuracao

router = APIRouter(tags=["config"])


class ConfigIn(BaseModel):
    provedor: str
    api_key: str | None = None  # None = manter a chave atual
    base_url: str = ""
    limite_contexto_tokens: int = 0
    gatilho_compressao_pct: int = 85
    alvo_reducao_pct: int = 50


def _publica(cfg: dict) -> dict:
    # A api_key nunca sai da API.
    return {
        **{k: v for k, v in cfg.items() if k != "api_key"},
        "api_key_definida": bool(cfg.get("api_key")),
        "provedores": PROVEDORES,
    }


@router.get("/config")
def obter_config():
    return _publica(carregar_configuracao())


@router.put("/config")
def salvar_config(body: ConfigIn):
    atual = carregar_configuracao()
    novo = {**atual, **body.model_dump(exclude={"api_key"})}
    if body.api_key is not None:
        novo["api_key"] = body.api_key
    salvar_configuracao(novo)
    return _publica(novo)
