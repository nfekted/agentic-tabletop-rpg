from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import agente_valido
from rpg.config import obter_modificadores_jogador, salvar_modificadores_jogador
from rpg.fichas import (
    carregar_ficha, carregar_padrao, carregar_status_jogador, carregar_subarquivos_ficha,
    padrao_configurado, salvar_padrao, salvar_status_jogador, salvar_subarquivos_ficha,
)

router = APIRouter(tags=["fichas"])


class Base(BaseModel):
    nome: str = ""
    classe: str = ""
    passado_origem: str = ""


class Status(BaseModel):
    nome: str
    valor_atual: int = 0
    valor_max: int = 0
    cor: str = "#DC143C"


class ParNomeValor(BaseModel):
    nome: str
    valor: str = ""


class Habilidade(BaseModel):
    nome: str
    custo: str = ""
    descricao: str = ""


class Habilidades(BaseModel):
    habilidades: list[Habilidade] = []
    poderes: list[Habilidade] = []
    passivas: list[Habilidade] = []


class Item(BaseModel):
    nome: str
    maos: int | None = None
    peso: float | None = None
    alcance: str = ""
    dano: str = ""
    porcentagem_crit: int | None = None
    multiplicador_critico: float | None = None
    descricao: str = ""


class Itens(BaseModel):
    tamanho_mochila: int = 5
    equipamento: list[Item] = []
    mochila: list[Item] = []


class Personalidade(BaseModel):
    tratamento_personalidade: str = ""
    medos_gatilhos: str = ""
    segredos_pessoais: str = ""


class PadraoStatus(BaseModel):
    nome: str
    cor: str = "#DC143C"


class PadraoAtributo(BaseModel):
    nome: str


class PadraoIn(BaseModel):
    status: list[PadraoStatus] = []
    atributos: list[PadraoAtributo] = []


class AjusteStatus(BaseModel):
    nome: str
    delta: int


class FichaIn(BaseModel):
    modificadores: str = ""
    base: Base
    status: list[Status]
    atributos: list[ParNomeValor]
    pericias: list[ParNomeValor]
    habilidades: Habilidades
    itens: Itens
    personalidade: Personalidade


def _ficha(nome: str) -> dict:
    return {**carregar_subarquivos_ficha(nome), "modificadores": obter_modificadores_jogador(nome)}


def _padrao() -> dict:
    return {**carregar_padrao(), "configurado": padrao_configurado()}


@router.get("/padrao-ficha")
def obter_padrao():
    return _padrao()


@router.put("/padrao-ficha")
def salvar_padrao_ficha(body: PadraoIn):
    salvar_padrao(body.model_dump())
    return _padrao()


@router.get("/fichas/{nome}")
def obter(nome: str):
    return _ficha(agente_valido(nome))


@router.put("/fichas/{nome}")
def salvar(nome: str, body: FichaIn):
    nome = agente_valido(nome)
    dados = body.model_dump(exclude={"modificadores"})
    salvar_subarquivos_ficha(nome, dados)
    salvar_modificadores_jogador(nome, body.modificadores)
    return _ficha(nome)


@router.post("/fichas/{nome}/status/ajustar")
def ajustar_status(nome: str, body: AjusteStatus):
    # Soma o delta ao valor atual do status, entre 0 e o máximo.
    nome = agente_valido(nome)
    status = carregar_status_jogador(nome)
    alvo = next((s for s in status if s["nome"] == body.nome), None)
    if not alvo:
        raise HTTPException(404, "Status não encontrado.")
    alvo["valor_atual"] = max(0, min(alvo["valor_max"], alvo["valor_atual"] + body.delta))
    salvar_status_jogador(nome, status)
    return status


@router.get("/fichas/{nome}/consolidada")
def consolidada(nome: str):
    return {"markdown": carregar_ficha(agente_valido(nome))}
