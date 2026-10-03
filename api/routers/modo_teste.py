from fastapi import APIRouter
from pydantic import BaseModel

from rpg import modo_teste

router = APIRouter(tags=["modo-teste"])


class AtivoIn(BaseModel):
    ativo: bool


@router.get("/modo-teste")
def estado():
    return {"ativo": modo_teste.ativo()}


@router.put("/modo-teste")
def definir(body: AtivoIn):
    modo_teste.definir(body.ativo)
    return estado()
