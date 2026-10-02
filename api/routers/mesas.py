from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import trava_mestre, trava_turno
from rpg.mesas_manager import info_mesa, listar_mesas, mesa_existe, restaurar_mesa, salvar_mesa
from services import sessao

router = APIRouter(tags=["mesas"])


class NomeIn(BaseModel):
    nome: str


@router.get("/mesas")
def listar():
    saida = []
    for nome in listar_mesas():
        mtime, tamanho = info_mesa(nome)
        saida.append({
            "nome": nome,
            "atualizada_em": datetime.fromtimestamp(mtime).isoformat(timespec="seconds"),
            "tamanho": tamanho,
        })
    return saida


@router.post("/mesas")
def salvar(body: NomeIn):
    with trava_mestre(), trava_turno():
        ok, msg = salvar_mesa(body.nome)
        if not ok:
            raise HTTPException(400, msg)
    return {"mensagem": msg}


@router.post("/mesas/{nome}/restaurar")
def restaurar(nome: str):
    if not mesa_existe(nome):
        raise HTTPException(404, "Mesa não encontrada.")
    with trava_mestre(), trava_turno():
        ok, msg = restaurar_mesa(nome)
        if not ok:
            raise HTTPException(400, msg)
        sessao.resetar()  # histórico, falas e pendências não fazem parte do backup
    return {"mensagem": msg}
