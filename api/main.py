# API FastAPI da Mesa de RPG. Inicie a partir da raiz do projeto:
#   uvicorn api.main:app --reload --port 8000
import asyncio
import os
import sys
from contextlib import asynccontextmanager

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from services import eventos  # noqa: E402
from services.sessao import ErroNegocio  # noqa: E402
from api.routers import (  # noqa: E402
    config, jogadores, fichas, regras, cenas, tokens, memoria, turno, mesas, mestre, sessao,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    eventos.iniciar(asyncio.get_running_loop())
    yield


app = FastAPI(title="Mesa de RPG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErroNegocio)
async def erro_negocio(_: Request, exc: ErroNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


for r in (config, jogadores, fichas, regras, cenas, tokens, memoria, turno, mesas, mestre, sessao):
    app.include_router(r.router, prefix="/api")

# Produção: se o front foi compilado (npm run build), a API também o serve.
_DIST = os.path.join(RAIZ, "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    def spa(caminho: str):
        arquivo = os.path.join(_DIST, caminho)
        if caminho and os.path.isfile(arquivo) and os.path.commonpath([_DIST, os.path.abspath(arquivo)]) == _DIST:
            return FileResponse(arquivo)
        return FileResponse(os.path.join(_DIST, "index.html"))
