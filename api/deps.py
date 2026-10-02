# Utilidades compartilhadas pelas rotas: validação de nomes (anti path traversal) e locks.
import re
from contextlib import contextmanager

from fastapi import HTTPException

from rpg.config import carregar_agentes
from services.sessao import LOCK_MESTRE, LOCK_TURNO

_NOME_ARQUIVO = re.compile(r"^[\w\-][\w\-. ]*$", re.UNICODE)


def agente_valido(nome: str) -> str:
    # Devolve o nome canônico do jogador (como está em jogadores.json) ou 404.
    for ag in carregar_agentes():
        if ag.lower() == nome.lower():
            return ag
    raise HTTPException(404, f"Jogador '{nome}' não encontrado.")


def nome_arquivo_valido(nome: str) -> str:
    nome = (nome or "").strip()
    if not _NOME_ARQUIVO.match(nome) or ".." in nome:
        raise HTTPException(400, "Nome inválido.")
    return nome


@contextmanager
def trava_mestre():
    # Uma ação do mestre/LLM por vez. Em vez de enfileirar, avisa que há outra em andamento.
    if not LOCK_MESTRE.acquire(blocking=False):
        raise HTTPException(409, "Outra ação está em andamento. Aguarde terminar.")
    try:
        yield
    finally:
        LOCK_MESTRE.release()


@contextmanager
def trava_turno():
    with LOCK_TURNO:
        yield
