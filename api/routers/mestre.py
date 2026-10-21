import os
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.deps import agente_valido, exigir_fila_livre, trava_mestre
from rpg.historico import separar
from rpg.imagens import salvar_imagem_upload
from api.routers.sessao import sessao_publica
from services import desfazer, fila, mestre

router = APIRouter(tags=["mestre"])

_MAX_IMAGEM = 10 * 1024 * 1024


class MotivoIn(BaseModel):
    motivo: str


def _resp(mensagem: str | None = None) -> dict:
    return {"mensagem": mensagem, "sessao": sessao_publica()}


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
    exigir_fila_livre()
    with trava_mestre():
        fila.enfileirar_finalizar()
        return _resp()


@router.post("/rodada/cancelar")
def cancelar(body: MotivoIn):
    with trava_mestre():
        return _resp(mestre.cancelar_rodada(body.motivo.strip() or "Sem motivo informado"))


@contextmanager
def _imagem_da_fila(imagem: UploadFile | None):
    # A imagem fica guardada até a fila terminar (ela apaga); só é removida aqui se a fila não chegar a nascer.
    caminho = _salvar_imagem(imagem)
    try:
        yield caminho
    except BaseException:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)
        raise


@router.post("/mestre/falar-todos")
def falar_todos(
    comando: Annotated[str, Form()],
    silencioso: Annotated[bool, Form()] = False,
    imagem: Annotated[UploadFile | None, File()] = None,
):
    comando = _texto(comando)
    if silencioso:
        # só registra na memória: ninguém responde (sem fila, sem LLM)
        with trava_mestre():
            mestre.preparar_falar_todos(comando)
            return _resp("Registrado, sem resposta dos jogadores.")
    exigir_fila_livre()
    with trava_mestre(), _imagem_da_fila(imagem) as caminho:
        fila.enfileirar_falar_todos(comando, caminho)
        return _resp()


@router.post("/mestre/falar-direcionado")
def falar_direcionado(
    comando: Annotated[str, Form()],
    alvos: Annotated[list[str], Form()],
    privado: Annotated[bool, Form()] = False,
    silencioso: Annotated[bool, Form()] = False,
    imagem: Annotated[UploadFile | None, File()] = None,
):
    comando = _texto(comando)
    presentes = [agente_valido(a) for a in alvos]
    if silencioso:
        with trava_mestre():
            mestre.preparar_falar_direcionado(presentes, privado, comando)
            return _resp("Registrado, sem resposta dos jogadores.")
    exigir_fila_livre()
    with trava_mestre(), _imagem_da_fila(imagem) as caminho:
        fila.enfileirar_falar_direcionado(presentes, privado, comando, caminho)
        return _resp()


@router.post("/pendencias/chamada/{chamada_id}/aprovar")
def aprovar_chamada(chamada_id: str):
    with trava_mestre():
        fila.enfileirar_chamada(chamada_id)
        return _resp()


@router.post("/pendencias/chamada/{chamada_id}/descartar")
def descartar_chamada(chamada_id: str):
    with trava_mestre():
        return _resp(mestre.descartar_chamada(chamada_id))


@router.post("/mestre/desfazer")
def desfazer_ultima():
    with trava_mestre():
        _, linha = separar(desfazer.reverter())
        # fala do mestre: devolve o texto para o campo de envio ("Mestre (para A, B): texto")
        texto = linha.split("): ", 1)[1] if linha.startswith("Mestre (para ") and "): " in linha else None
        return {**_resp("Última linha desfeita."), "texto": texto}
