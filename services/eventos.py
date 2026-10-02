# Barramento de eventos (SSE): serviços síncronos publicam, clientes assinam via /api/eventos.
import asyncio

_clientes: set[asyncio.Queue] = set()
_loop: asyncio.AbstractEventLoop | None = None


def iniciar(loop: asyncio.AbstractEventLoop):
    global _loop
    _loop = loop


def assinar() -> asyncio.Queue:
    fila: asyncio.Queue = asyncio.Queue(maxsize=200)
    _clientes.add(fila)
    return fila


def cancelar(fila: asyncio.Queue):
    _clientes.discard(fila)


def _distribuir(evento: dict):
    for fila in list(_clientes):
        try:
            fila.put_nowait(evento)
        except asyncio.QueueFull:
            pass


def publicar(tipo: str, **dados):
    # Seguro para chamar de threads do threadpool do FastAPI.
    if _loop is None or _loop.is_closed():
        return
    _loop.call_soon_threadsafe(_distribuir, {"tipo": tipo, **dados})
