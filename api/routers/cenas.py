from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import nome_arquivo_valido
from rpg.cenas import deletar_cena, ler_cena, listar_cenas, nome_seguro, salvar_cena

router = APIRouter(tags=["cenas"])


class CenaIn(BaseModel):
    nome: str
    conteudo: str = ""


class ConteudoIn(BaseModel):
    conteudo: str


@router.get("/cenas")
def listar():
    return listar_cenas()


@router.post("/cenas", status_code=201)
def criar(body: CenaIn):
    nome = nome_arquivo_valido(nome_seguro(body.nome))
    salvar_cena(nome, body.conteudo)
    return {"nome": nome}


@router.get("/cenas/{nome}")
def ler(nome: str):
    nome = nome_arquivo_valido(nome)
    if nome not in listar_cenas():
        raise HTTPException(404, "Cena não encontrada.")
    return {"nome": nome, "conteudo": ler_cena(nome)}


@router.put("/cenas/{nome}")
def salvar(nome: str, body: ConteudoIn):
    salvar_cena(nome_arquivo_valido(nome), body.conteudo)
    return {"ok": True}


@router.delete("/cenas/{nome}")
def excluir(nome: str):
    if not deletar_cena(nome_arquivo_valido(nome)):
        raise HTTPException(404, "Cena não encontrada.")
    return {"ok": True}
