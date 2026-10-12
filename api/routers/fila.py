from fastapi import APIRouter

from services import fila

router = APIRouter(tags=["fila"])


@router.get("/fila")
def obter():
    return fila.estado()


@router.post("/fila/continuar")
def continuar():
    fila.continuar()
    return fila.estado()


@router.post("/fila/cancelar")
def cancelar():
    fila.cancelar()
    return fila.estado()
