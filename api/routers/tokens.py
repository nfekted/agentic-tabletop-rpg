from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import nome_arquivo_valido
from rpg.tokens_manager import (
    CATEGORIAS,
    caminho_imagem_token,
    carregar_token,
    criar_token,
    excluir_token,
    garantir_estrutura_tokens,
    listar_tokens,
    remover_imagem_token,
    salvar_imagem_token,
    salvar_token,
)

router = APIRouter(tags=["tokens"])

_MAX_IMAGEM = 8 * 1024 * 1024


class NovoToken(BaseModel):
    nome: str
    conteudo: str = ""


class ConteudoIn(BaseModel):
    conteudo: str


def _cat(categoria: str) -> str:
    if categoria not in CATEGORIAS:
        raise HTTPException(404, "Categoria inexistente.")
    return categoria


def _existente(categoria: str, arquivo: str) -> str:
    arquivo = nome_arquivo_valido(arquivo)
    if arquivo not in listar_tokens(_cat(categoria)):
        raise HTTPException(404, "Token não encontrado.")
    return arquivo


@router.get("/tokens")
def categorias():
    garantir_estrutura_tokens()
    return {
        c: {
            "rotulo": r,
            "arquivos": [
                {"arquivo": a, "tem_imagem": caminho_imagem_token(c, a) is not None}
                for a in listar_tokens(c)
            ],
        }
        for c, r in CATEGORIAS.items()
    }


@router.post("/tokens/{categoria}", status_code=201)
def criar(categoria: str, body: NovoToken):
    arquivo = criar_token(_cat(categoria), body.nome, body.conteudo)
    if not arquivo:
        raise HTTPException(400, "Nome inválido ou já existente.")
    return {"arquivo": arquivo}


@router.get("/tokens/{categoria}/{arquivo}")
def ler(categoria: str, arquivo: str):
    arquivo = _existente(categoria, arquivo)
    return {"arquivo": arquivo, "conteudo": carregar_token(categoria, arquivo)}


@router.put("/tokens/{categoria}/{arquivo}")
def salvar(categoria: str, arquivo: str, body: ConteudoIn):
    salvar_token(categoria, _existente(categoria, arquivo), body.conteudo)
    return {"ok": True}


@router.delete("/tokens/{categoria}/{arquivo}")
def excluir(categoria: str, arquivo: str):
    excluir_token(categoria, _existente(categoria, arquivo))
    return {"ok": True}


@router.get("/tokens/{categoria}/{arquivo}/imagem")
def imagem(categoria: str, arquivo: str):
    caminho = caminho_imagem_token(_cat(categoria), nome_arquivo_valido(arquivo))
    if not caminho:
        raise HTTPException(404, "Token sem imagem.")
    return FileResponse(caminho)


@router.post("/tokens/{categoria}/{arquivo}/imagem")
def enviar_imagem(categoria: str, arquivo: str, imagem: UploadFile = File(...)):
    arquivo = _existente(categoria, arquivo)
    dados = imagem.file.read(_MAX_IMAGEM + 1)
    if len(dados) > _MAX_IMAGEM:
        raise HTTPException(413, "Imagem maior que 8 MB.")
    if not salvar_imagem_token(categoria, arquivo, imagem.filename, dados):
        raise HTTPException(400, "Arquivo vazio.")
    return {"ok": True}


@router.delete("/tokens/{categoria}/{arquivo}/imagem")
def remover_imagem(categoria: str, arquivo: str):
    remover_imagem_token(categoria, _existente(categoria, arquivo))
    return {"ok": True}
