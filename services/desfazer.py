# Desfazer a última linha do histórico da cena (fala do mestre ou resposta de um jogador).
# Antes de cada linha nova guardamos o tamanho da rodada de cada jogador e o estado da sessão; desfazer
# apaga o que foi gravado depois disso. Só a última linha pode ser desfeita (as anteriores, uma de cada vez).
import copy
import json
import os

from rpg.config import carregar_agentes
from rpg.memoria import _caminho_temp
from rpg.paths import ARQUIVOS
from services.sessao import ErroNegocio, obter, salvar

_CAMINHO = os.path.join(ARQUIVOS, "desfazer.json")
_CAMPOS = ("envolvidos", "pending_chamadas", "ultima_fala", "pensamentos", "seq_fala")


def _ler() -> list[dict]:
    try:
        with open(_CAMINHO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _gravar(registros: list[dict]):
    os.makedirs(ARQUIVOS, exist_ok=True)
    tmp = _CAMINHO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False)
    os.replace(tmp, _CAMINHO)


def registrar():
    # Chamar logo antes de uma operação que vai acrescentar uma linha ao histórico.
    s = obter()
    linha = len(s["historico"])
    registros = [r for r in _ler() if r["linha"] < linha]
    temp = {}
    for ag in carregar_agentes():
        caminho = _caminho_temp(ag)
        temp[ag] = os.path.getsize(caminho) if os.path.exists(caminho) else None
    registros.append({"linha": linha, "temp": temp, "estado": {c: copy.deepcopy(s[c]) for c in _CAMPOS}})
    _gravar(registros)


def invalidar():
    # Operações que reescrevem o histórico ou a memória no meio (e não só acrescentam) tornam os tamanhos guardados inválidos.
    if os.path.exists(_CAMINHO):
        os.remove(_CAMINHO)


def possivel() -> bool:
    registros = _ler()
    return bool(registros) and registros[-1]["linha"] == len(obter()["historico"]) - 1


def reverter() -> str:
    # Desfaz a última linha e devolve o texto dela.
    s = obter()
    if not s["rodada_ativa"] or not possivel():
        raise ErroNegocio("Não há nada para desfazer.")
    registros = _ler()
    r = registros.pop()
    linha = s["historico"][r["linha"]]

    for ag, tamanho in r["temp"].items():
        caminho = _caminho_temp(ag)
        if not os.path.exists(caminho):
            continue
        if tamanho is None:
            os.remove(caminho)
        else:
            with open(caminho, "r+b") as f:
                f.truncate(tamanho)

    del s["historico"][r["linha"]:]
    s.update(copy.deepcopy(r["estado"]))
    _gravar(registros)
    salvar()
    return linha
