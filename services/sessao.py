# Estado da mesa (rodada, histórico, pendências, balões). Único, global e persistido em
# arquivos/sessao.json — substitui o antigo st.session_state de domínio.
import copy
import json
import os
import threading

from services import eventos
from rpg.paths import ARQUIVOS

_CAMINHO = os.path.join(ARQUIVOS, "sessao.json")

# Lock das operações que mexem na sessão/LLM; turno.json tem o seu próprio.
LOCK_MESTRE = threading.RLock()
LOCK_TURNO = threading.RLock()

_PADRAO = {
    "historico": [],
    "rodada_ativa": False,
    "envolvidos": [],
    "pending_principal": None,
    "aguardando_redirect": None,
    "pending_redirects": [],
    "ultima_fala": {},
    "seq_fala": 0,
    "compressao_perguntada": {},
}

_estado: dict | None = None


class ErroNegocio(Exception):
    # Regra violada pelo pedido (vira HTTP 400/409 na API).
    pass


def obter() -> dict:
    global _estado
    if _estado is None:
        _estado = copy.deepcopy(_PADRAO)
        try:
            with open(_CAMINHO, "r", encoding="utf-8") as f:
                _estado.update(json.load(f))
        except Exception:
            pass
    return _estado


def salvar():
    os.makedirs(ARQUIVOS, exist_ok=True)
    tmp = _CAMINHO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obter(), f, indent=2, ensure_ascii=False)
    os.replace(tmp, _CAMINHO)
    eventos.publicar("sessao_atualizada")


def resetar():
    global _estado
    _estado = copy.deepcopy(_PADRAO)
    salvar()


def registrar_fala(agente: str, texto: str, aprovada: bool = True, privado: bool = False):
    # "seq" identifica cada fala; permite ao front fechar só a fala atual.
    s = obter()
    s["seq_fala"] += 1
    s["ultima_fala"][agente] = {
        "seq": s["seq_fala"],
        "texto": texto,
        "aprovada": aprovada,
        "privado": privado,
    }


def limpar_fala(agente: str):
    obter()["ultima_fala"].pop(agente, None)
