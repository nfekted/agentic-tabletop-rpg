from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import nome_arquivo_valido, trava_turno
from rpg.config import carregar_agentes
from rpg.tokens_manager import CATEGORIAS, listar_tokens
from rpg import turno as t

router = APIRouter(tags=["turno"])


class NomeIn(BaseModel):
    nome: str


class ParticipanteIn(BaseModel):
    participante_id: str


class TokenIn(BaseModel):
    categoria: str
    arquivo: str


class OrdemIn(BaseModel):
    ordem: int | None = None


class FilaIn(BaseModel):
    ids: list[str]  # participantes na ordem de iniciativa; os ausentes ficam sem ordem


class FichaTokenIn(BaseModel):
    conteudo: str
    status: list[dict] = []


def _estado() -> dict:
    if not t.turno_ativo():
        return {"ativo": False, "turno": None, "empates": []}
    dados = t.sincronizar_personagens(carregar_agentes())
    return {"ativo": True, "turno": dados, "empates": t.verificar_empates(dados)}


def _exigir_ativo() -> dict:
    dados = t.carregar_turno()
    if not dados:
        raise HTTPException(409, "Modo por turnos não está ativo.")
    return dados


@router.get("/turno")
def obter():
    with trava_turno():
        return _estado()


@router.post("/turno/iniciar")
def iniciar():
    with trava_turno():
        if not t.turno_ativo():
            t.iniciar_turno(carregar_agentes())
        return _estado()


@router.delete("/turno")
def encerrar():
    with trava_turno():
        t.encerrar_turno()
        return _estado()


@router.post("/turno/proxima")
def proxima():
    with trava_turno():
        ok, msg = t.avancar_proxima_acao(_exigir_ativo())
        return {"ok": ok, "mensagem": msg, **_estado()}


@router.post("/turno/areas", status_code=201)
def criar_area(body: NomeIn):
    with trava_turno():
        _exigir_ativo()
        if not t.adicionar_area(body.nome):
            raise HTTPException(400, "Nome da área inválido.")
        return _estado()


@router.delete("/turno/areas/{area_id}")
def remover_area(area_id: str):
    with trava_turno():
        _exigir_ativo()
        if not t.remover_area(area_id):
            raise HTTPException(404, "Área não encontrada.")
        return _estado()


@router.put("/turno/areas/{area_id}/participantes")
def vincular(area_id: str, body: ParticipanteIn):
    with trava_turno():
        _exigir_ativo()
        if not t.vincular_participante(area_id, body.participante_id):
            raise HTTPException(404, "Área não encontrada.")
        return _estado()


@router.delete("/turno/participantes/{participante_id}/area")
def desvincular(participante_id: str):
    with trava_turno():
        _exigir_ativo()
        t.desvincular_participante(participante_id)
        return _estado()


@router.post("/turno/tokens", status_code=201)
def adicionar_token(body: TokenIn):
    if body.categoria not in CATEGORIAS:
        raise HTTPException(404, "Categoria inexistente.")
    arquivo = nome_arquivo_valido(body.arquivo)
    if arquivo not in listar_tokens(body.categoria):
        raise HTTPException(404, "Token não encontrado.")
    with trava_turno():
        _exigir_ativo()
        t.adicionar_token_ao_turno(body.categoria, arquivo)
        return _estado()


@router.delete("/turno/tokens/{token_id}")
def remover_token(token_id: str):
    with trava_turno():
        _exigir_ativo()
        if not t.remover_token_do_turno(token_id):
            raise HTTPException(404, "Token não encontrado.")
        return _estado()


@router.put("/turno/tokens/{token_id}/ficha")
def ficha_token(token_id: str, body: FichaTokenIn):
    with trava_turno():
        _exigir_ativo()
        if not t.atualizar_ficha_token(token_id, body.model_dump()):
            raise HTTPException(404, "Token não encontrado.")
        return _estado()


@router.put("/turno/participantes/{participante_id}/ordem")
def ordem(participante_id: str, body: OrdemIn):
    with trava_turno():
        _exigir_ativo()
        if not t.atualizar_ordem_participante(participante_id, body.ordem):
            raise HTTPException(404, "Participante não encontrado.")
        return _estado()


@router.put("/turno/fila")
def fila(body: FilaIn):
    # Reordenação por arrastar: a posição na lista vira a ordem de iniciativa (1..n).
    with trava_turno():
        dados = _exigir_ativo()
        todos = {p["id"] for p in dados["personagens"] + dados["tokens"]}
        if any(i not in todos for i in body.ids) or len(set(body.ids)) != len(body.ids):
            raise HTTPException(400, "Lista de participantes inválida.")
        for p in dados["personagens"] + dados["tokens"]:
            p["ordem"] = body.ids.index(p["id"]) + 1 if p["id"] in body.ids else None
        t.salvar_turno(dados)
        return _estado()
