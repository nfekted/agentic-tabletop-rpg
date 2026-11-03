from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import agente_valido, agente_vivo, checar_limites, trava_mestre
from rpg.memoria import GerenciadorMemoriaRPG, obter_arquivos_memoria
from rpg.metricas import calcular_contexto
from services import sessao

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


class EncerrarIn(BaseModel):
    gerar: bool = True


@router.post("/memoria/{nome}/encerrar")
def encerrar(nome: str, body: EncerrarIn):
    # Fim de missão de um personagem: compila a memória até o mesa.txt e, se pedido, sugere o resumo da missão.
    nome = agente_vivo(nome)
    if sessao.obter()["rodada_ativa"]:
        raise HTTPException(400, "Encerre a rodada atual antes de encerrar a mesa.")
    with trava_mestre():
        checar_limites(2 + body.gerar)
        GerenciadorMemoriaRPG.encerrar_memoria(nome)
        resumo = GerenciadorMemoriaRPG.resumir_missao(nome) if body.gerar else ""
    return {"resumo": resumo}


@router.post("/memoria/{nome}/comprimir")
def comprimir(nome: str):
    nome = agente_valido(nome)
    with trava_mestre():
        checar_limites(2)  # estimativa: resumo de cenas + redução do mesa.txt
        ok, msg = GerenciadorMemoriaRPG.comprimir_memoria(nome)
    return {"ok": ok, "mensagem": msg}
