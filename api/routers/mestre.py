import os
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.deps import agente_valido, trava_mestre
from rpg.imagens import salvar_imagem_upload
from services import mestre
from services.sessao import obter

router = APIRouter(tags=["mestre"])

_MAX_IMAGEM = 10 * 1024 * 1024


class MotivoIn(BaseModel):
    motivo: str


def _resp(mensagem: str | None = None) -> dict:
    return {"mensagem": mensagem, "sessao": obter()}


def _salvar_imagem(imagem: UploadFile | None) -> str | None:
    if imagem is None or not imagem.filename:
        return None
    dados = imagem.file.read(_MAX_IMAGEM + 1)
    if len(dados) > _MAX_IMAGEM:
        raise HTTPException(413, "Imagem maior que 10 MB.")
    return salvar_imagem_upload(imagem.filename, dados)


def _texto(comando: str) -> str:
    comando = comando.strip()
    if not comando:
        raise HTTPException(400, "Digite a mensagem do mestre.")
    return comando


@router.post("/rodada/iniciar")
def iniciar():
    with trava_mestre():
        return _resp(mestre.iniciar_rodada())


@router.post("/rodada/finalizar")
def finalizar():
    with trava_mestre():
        return _resp(mestre.finalizar_rodada())


@router.post("/rodada/cancelar")
def cancelar(body: MotivoIn):
    with trava_mestre():
        return _resp(mestre.cancelar_rodada(body.motivo.strip() or "Sem motivo informado"))


@router.post("/mestre/falar-todos")
def falar_todos(
    comando: Annotated[str, Form()],
    imagem: Annotated[UploadFile | None, File()] = None,
):
    comando = _texto(comando)
    with trava_mestre():
        caminho = _salvar_imagem(imagem)
        try:
            return _resp(mestre.falar_com_todos(comando, caminho))
        finally:
            if caminho and os.path.exists(caminho):
                os.remove(caminho)


@router.post("/mestre/falar-direcionado")
def falar_direcionado(
    comando: Annotated[str, Form()],
    alvos: Annotated[list[str], Form()],
    privado: Annotated[bool, Form()] = False,
    imagem: Annotated[UploadFile | None, File()] = None,
):
    comando = _texto(comando)
    presentes = [agente_valido(a) for a in alvos]
    with trava_mestre():
        caminho = _salvar_imagem(imagem)
        try:
            return _resp(mestre.falar_direcionado(presentes, privado, comando, caminho))
        finally:
            if caminho and os.path.exists(caminho):
                os.remove(caminho)


@router.post("/pendencias/chamada/{chamada_id}/aprovar")
def aprovar_chamada(chamada_id: str):
    with trava_mestre():
        return _resp(mestre.aprovar_chamada(chamada_id))


@router.post("/pendencias/chamada/{chamada_id}/descartar")
def descartar_chamada(chamada_id: str):
    with trava_mestre():
        return _resp(mestre.descartar_chamada(chamada_id))
