from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import trava_mestre, trava_turno
from rpg.mesas_manager import (
    definir_nome_mesa, eh_autosave, excluir_mesa, importar_base, info_mesa, listar_mesas, mesa_existe, nome_mesa_atual, reiniciar_mesa, resetar_mesa,
    restaurar_mesa, salvar_mesa,
)
from services import fila, sessao

router = APIRouter(tags=["mesas"])


class NomeIn(BaseModel):
    nome: str


class ImportarBaseIn(BaseModel):
    backup: str
    categorias: list[str]
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
            "autosave": eh_autosave(nome),
        })
    return saida


@router.get("/mesa")
def mesa_atual():
    return {"nome": nome_mesa_atual()}


@router.put("/mesa")
def definir_mesa(body: NomeIn):
    ok, resultado = definir_nome_mesa(body.nome)
    if not ok:
        raise HTTPException(400, resultado)
    return {"nome": resultado}


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
        sessao.recarregar()  # a sessão vem do backup; mesas antigas, sem ela, começam do zero
        fila.resetar()
    return {"mensagem": msg}


@router.delete("/mesas/{nome}")
def excluir(nome: str):
    with trava_mestre(), trava_turno():
        ok, msg = excluir_mesa(nome)
        if not ok:
            raise HTTPException(404 if "não encontrado" in msg else 400, msg)
    return {"mensagem": msg}


@router.post("/mesas/importar-base")
def importar(body: ImportarBaseIn):
    with trava_mestre(), trava_turno():
        ok, msg = importar_base(body.backup, body.categorias, body.nome)
        if not ok:
            raise HTTPException(400, msg)
        sessao.resetar()
        fila.resetar()
    return {"mensagem": msg}


@router.post("/mesas/resetar")
def resetar():
    with trava_mestre(), trava_turno():
        ok, msg = resetar_mesa()
        if not ok:
            raise HTTPException(400, msg)
        sessao.resetar()
        fila.resetar()
    return {"mensagem": msg}


@router.post("/mesas/reiniciar")
def reiniciar():
    with trava_mestre(), trava_turno():
        ok, msg = reiniciar_mesa()
        if not ok:
            raise HTTPException(400, msg)
        sessao.resetar()
        fila.resetar()
    return {"mensagem": msg}
