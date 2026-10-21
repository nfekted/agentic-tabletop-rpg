import os

from fastapi import APIRouter
from pydantic import BaseModel

from rpg.paths import ARQUIVOS

router = APIRouter(tags=["anotacoes"])

# fica em arquivos/: entra no salvar/restaurar mesa
CAMINHO = os.path.join(ARQUIVOS, "anotacoes_mestre.txt")


class AnotacoesIn(BaseModel):
    conteudo: str


@router.get("/anotacoes")
def ler():
    if not os.path.isfile(CAMINHO):
        return {"conteudo": ""}
    with open(CAMINHO, "r", encoding="utf-8") as f:
        return {"conteudo": f.read()}


@router.put("/anotacoes")
def salvar(body: AnotacoesIn):
    os.makedirs(ARQUIVOS, exist_ok=True)
    tmp = CAMINHO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(body.conteudo)
    os.replace(tmp, CAMINHO)
    return {"ok": True}
