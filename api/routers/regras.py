from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import nome_arquivo_valido
from rpg.fichas import (
    ARQUIVO_BASE,
    carregar_regra,
    criar_arquivo_regra,
    definir_regra_ativa,
    listar_arquivos_regras,
    obter_regra_ativa,
    remover_arquivo_regra,
    salvar_regra,
)

router = APIRouter(tags=["regras"])


class NomeIn(BaseModel):
    nome: str


class ConteudoIn(BaseModel):
    conteudo: str


def _existente(arquivo: str) -> str:
    arquivo = nome_arquivo_valido(arquivo)
    if arquivo != ARQUIVO_BASE and arquivo not in listar_arquivos_regras():
        raise HTTPException(404, "Conjunto de regras não encontrado.")
    return arquivo


@router.get("/regras")
def listar():
    arquivos = listar_arquivos_regras()
    return {"base": ARQUIVO_BASE, "arquivos": arquivos, "ativa": obter_regra_ativa()}


@router.post("/regras", status_code=201)
def criar(body: NomeIn):
    arquivo = criar_arquivo_regra(body.nome)
    if not arquivo:
        raise HTTPException(400, "Nome inválido ou já existente.")
    return {"arquivo": arquivo}


@router.put("/regras/ativa")
def ativar(body: NomeIn):
    if body.nome == ARQUIVO_BASE:
        raise HTTPException(400, "A base já é sempre enviada; escolha um conjunto.")
    definir_regra_ativa(_existente(body.nome))
    return {"ativa": body.nome}


@router.get("/regras/{arquivo}")
def ler(arquivo: str):
    return {"arquivo": arquivo, "conteudo": carregar_regra(_existente(arquivo))}


@router.put("/regras/{arquivo}")
def salvar(arquivo: str, body: ConteudoIn):
    salvar_regra(_existente(arquivo), body.conteudo)
    return {"ok": True}


@router.delete("/regras/{arquivo}")
def excluir(arquivo: str):
    if _existente(arquivo) == ARQUIVO_BASE:
        raise HTTPException(400, "A base não pode ser excluída.")
    remover_arquivo_regra(arquivo)
    return {"ok": True}
