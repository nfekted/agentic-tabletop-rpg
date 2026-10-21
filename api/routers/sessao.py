import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services import compressao, desfazer, eventos
from services.sessao import obter

router = APIRouter(tags=["sessao"])


def sessao_publica() -> dict:
    # pode_desfazer é derivado (não é gravado na sessão): a última linha do histórico tem como ser desfeita
    s = obter()
    return {**s, "pode_desfazer": s["rodada_ativa"] and desfazer.possivel()}


@router.get("/sessao")
def sessao():
    return sessao_publica()


@router.get("/compressao/pendente")
def compressao_pendente():
    return compressao.proxima_pergunta()


@router.get("/eventos")
async def stream():
    fila = eventos.assinar()

    async def gerador():
        try:
            yield ": conectado\n\n"
            while True:
                try:
                    ev = await asyncio.wait_for(fila.get(), timeout=15)
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            eventos.cancelar(fila)

    return StreamingResponse(
        gerador(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
