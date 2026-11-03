from fastapi import APIRouter, HTTPException
from typing import Literal

from pydantic import BaseModel

from api.deps import agente_valido
from rpg.config import obter_modificadores_jogador, salvar_modificadores_jogador
from services import mestre
from rpg.fichas import (
    anexar_missao, carregar_ficha, carregar_padrao, carregar_status_jogador, carregar_subarquivos_ficha,
    padrao_configurado, salvar_padrao, salvar_status_jogador, salvar_subarquivos_ficha, transferir_item,
)

router = APIRouter(tags=["fichas"])


class Base(BaseModel):
    nome: str = ""
    classe: str = ""
    passado_origem: str = ""
    detalhes_adicionais: str = ""
    missoes_anteriores: str = ""


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


class Situacao(BaseModel):
    pct: int = 0
    nome: str = ""


class PadraoStatus(BaseModel):
    nome: str
    cor: str = "#DC143C"
    situacoes: list[Situacao] = []


class PadraoAtributo(BaseModel):
    nome: str


class PadraoIn(BaseModel):
    status: list[PadraoStatus] = []
    atributos: list[PadraoAtributo] = []


class AjusteStatus(BaseModel):
    nome: str
    delta: int


class MissaoIn(BaseModel):
    texto: str
    titulo: str = ""


class TransferenciaItem(BaseModel):
    destino: str
    zona: Literal["equipamento", "mochila"]
    indice: int
    nome: str


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


@router.post("/fichas/{nome}/itens/transferir")
def transferir(nome: str, body: TransferenciaItem):
    # O item vai para a mochila do destino; as duas fichas são gravadas na hora.
    origem, destino = agente_valido(nome), agente_valido(body.destino)
    if origem == destino:
        raise HTTPException(400, "Escolha outro personagem.")
    try:
        itens_origem, _ = transferir_item(origem, destino, body.zona, body.indice, body.nome)
    except ValueError as e:
        raise HTTPException(409, str(e))
    mestre.registrar_transferencia(origem, destino, body.nome)
    return {"itens": itens_origem, "destino": destino}


@router.post("/fichas/{nome}/missao")
def registrar_missao(nome: str, body: MissaoIn):
    try:
        anexar_missao(agente_valido(nome), body.texto, body.titulo)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


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
