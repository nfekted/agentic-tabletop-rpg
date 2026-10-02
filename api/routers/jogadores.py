import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import agente_valido, trava_mestre
from rpg.config import (
    adicionar_agente,
    carregar_agentes,
    obter_modificadores_jogador,
    salvar_modificadores_jogador,
)
from rpg.fichas import carregar_status_jogador
from rpg.imagens import caminho_avatar, remover_avatar_jogador, salvar_avatar_jogador
from rpg.metricas import calcular_contexto
from services.personagens import excluir_personagem

router = APIRouter(tags=["jogadores"])

_MAX_AVATAR = 8 * 1024 * 1024


class NovoJogador(BaseModel):
    nome: str


class Modificadores(BaseModel):
    modificadores: str


def _card(nome: str) -> dict:
    av = caminho_avatar(nome)
    return {
        "nome": nome,
        "modificadores": obter_modificadores_jogador(nome),
        "avatar_v": int(os.path.getmtime(av)) if av else None,
        "status": carregar_status_jogador(nome),
        "contexto": calcular_contexto(nome),
    }


@router.get("/jogadores")
def listar():
    return [_card(n) for n in carregar_agentes()]


@router.post("/jogadores", status_code=201)
def criar(body: NovoJogador):
    if not adicionar_agente(body.nome):
        raise HTTPException(400, "Nome inválido (use letras/números/_, sem espaços) ou já existente.")
    return _card(body.nome.strip())


@router.delete("/jogadores/{nome}")
def excluir(nome: str):
    nome = agente_valido(nome)
    with trava_mestre():
        excluir_personagem(nome)
    return {"ok": True}


@router.put("/jogadores/{nome}/modificadores")
def modificadores(nome: str, body: Modificadores):
    nome = agente_valido(nome)
    salvar_modificadores_jogador(nome, body.modificadores)
    return _card(nome)


@router.get("/jogadores/{nome}/avatar")
def avatar(nome: str):
    nome = agente_valido(nome)
    caminho = caminho_avatar(nome)
    if not caminho:
        raise HTTPException(404, "Sem foto.")
    return FileResponse(caminho)


@router.post("/jogadores/{nome}/avatar")
def enviar_avatar(nome: str, arquivo: UploadFile = File(...)):
    nome = agente_valido(nome)
    dados = arquivo.file.read(_MAX_AVATAR + 1)
    if len(dados) > _MAX_AVATAR:
        raise HTTPException(413, "Imagem maior que 8 MB.")
    if not salvar_avatar_jogador(nome, arquivo.filename, dados):
        raise HTTPException(400, "Arquivo vazio.")
    return _card(nome)


@router.delete("/jogadores/{nome}/avatar")
def remover_avatar(nome: str):
    nome = agente_valido(nome)
    remover_avatar_jogador(nome)
    return _card(nome)
