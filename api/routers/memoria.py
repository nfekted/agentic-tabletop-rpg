from fastapi import APIRouter

from api.deps import agente_valido, trava_mestre
from rpg.memoria import GerenciadorMemoriaRPG, obter_arquivos_memoria
from rpg.metricas import calcular_contexto

router = APIRouter(tags=["memoria"])


@router.get("/memoria/{nome}")
def ler(nome: str):
    m = obter_arquivos_memoria(agente_valido(nome))
    return {
        "rodada_atual": m["rodada_atual"],
        "rodadas": [{"arquivo": a, "conteudo": c} for a, c in m["rodadas"]],
        "cenas": [{"arquivo": a, "conteudo": c} for a, c in m["cenas"]],
        "mesa": m["mesa"],
    }


@router.get("/contexto/{nome}")
def contexto(nome: str):
    return calcular_contexto(agente_valido(nome))


@router.post("/memoria/{nome}/comprimir")
def comprimir(nome: str):
    nome = agente_valido(nome)
    with trava_mestre():
        ok, msg = GerenciadorMemoriaRPG.comprimir_memoria(nome)
    return {"ok": ok, "mensagem": msg}
