from fastapi import APIRouter
from pydantic import BaseModel

from api.deps import agente_valido
from rpg.config import obter_modificadores_jogador, salvar_modificadores_jogador
from rpg.fichas import carregar_ficha, carregar_subarquivos_ficha, salvar_subarquivos_ficha

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


@router.get("/fichas/{nome}/consolidada")
def consolidada(nome: str):
    return {"markdown": carregar_ficha(agente_valido(nome))}
