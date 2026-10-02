from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import nome_arquivo_valido
from rpg.fichas import (
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
    if arquivo not in listar_arquivos_regras():
        raise HTTPException(404, "Conjunto de regras não encontrado.")
    return arquivo


@router.get("/regras")
def listar():
    arquivos = listar_arquivos_regras()
    return {"arquivos": arquivos, "ativa": obter_regra_ativa() if arquivos else None}


@router.post("/regras", status_code=201)
def criar(body: NomeIn):
    arquivo = criar_arquivo_regra(body.nome)
    if not arquivo:
        raise HTTPException(400, "Nome inválido ou já existente.")
    return {"arquivo": arquivo}


@router.put("/regras/ativa")
def ativar(body: NomeIn):
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
    if not remover_arquivo_regra(_existente(arquivo)):
        raise HTTPException(400, "Não é possível excluir o único conjunto restante.")
    return {"ok": True}
