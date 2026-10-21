import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rpg import limites
from rpg.config import TIPOS_API, carregar_configuracao, obter_llm, salvar_configuracao

router = APIRouter(tags=["config"])


class ConfigIn(BaseModel):
    tipo_api: str
    modelo: str
    api_key: str | None = None  # None = manter a chave atual
    base_url: str = ""
    limite_contexto_tokens: int = 0
    gatilho_compressao_pct: int = 85
    alvo_reducao_pct: int = 50
    limite_rpm: int = 0
    limite_tpm: int = 0
    limite_rpd: int = 0
    fila_sempre_visivel: bool = False
    limite_resumo_combate: int = Field(2500, ge=0)


def _publica(cfg: dict) -> dict:
    # A api_key nunca sai da API.
    return {
        **{k: v for k, v in cfg.items() if k != "api_key"},
        "api_key_definida": bool(cfg.get("api_key")),
        "tipos_api": [{"id": k, "nome": v} for k, v in TIPOS_API.items()],
    }


@router.get("/config")
def obter_config():
    return _publica(carregar_configuracao())


@router.put("/config")
def salvar_config(body: ConfigIn):
    if body.tipo_api not in TIPOS_API:
        raise HTTPException(400, "Tipo de API inválido.")
    atual = carregar_configuracao()
    novo = {**atual, **body.model_dump(exclude={"api_key"})}
    if body.api_key is not None:
        novo["api_key"] = body.api_key
    salvar_configuracao(novo)
    return _publica(novo)


class TesteIn(BaseModel):
    tipo_api: str
    modelo: str
    api_key: str | None = None  # None/vazio = usar a chave salva
    base_url: str = ""


@router.post("/config/testar")
def testar_config(body: TesteIn):
    # Testa os valores do formulário sem salvar e sem contar nos limites.
    if body.tipo_api not in TIPOS_API:
        raise HTTPException(400, "Tipo de API inválido.")
    cfg = {**carregar_configuracao(), **body.model_dump(exclude={"api_key"})}
    if body.api_key:
        cfg["api_key"] = body.api_key
    inicio = time.monotonic()
    try:
        resp = obter_llm(0, cfg).invoke("Responda apenas: ok")
    except Exception as e:
        return {"ok": False, "mensagem": (str(e).strip() or type(e).__name__)[:400]}
    ms = round((time.monotonic() - inicio) * 1000)
    texto = resp.content if isinstance(resp.content, str) else str(resp.content)
    return {"ok": True, "ms": ms, "mensagem": f"Conectado em {ms} ms. Resposta: {texto.strip()[:80]}"}


class RpdIn(BaseModel):
    usado: int = Field(ge=0)


@router.put("/limites/rpd")
def definir_rpd(body: RpdIn):
    limites.definir_rpd(body.usado)
    return limites.estado()


@router.get("/limites")
def obter_limites():
    return limites.estado()
