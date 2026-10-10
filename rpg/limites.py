# Contadores de RPM / TPM / RPD das chamadas à LLM (limites opcionais; 0 = desligado).
# O minuto é uma janela deslizante de 60 s; o RPD é salvo em arquivos/limites.json com a data.
import json
import os
import threading
import time
from datetime import date, datetime, timedelta

from rpg.config import carregar_configuracao
from rpg.fichas import salvar_json
from rpg.metricas import CHARS_POR_TOKEN_PADRAO, _texto_da_mensagem, _usage
from rpg.paths import ARQUIVOS

JANELA_S = 60
_CAMINHO = os.path.join(ARQUIVOS, "limites.json")
_LOCK = threading.Lock()
_eventos: list[tuple[float, int]] = []  # (timestamp, tokens) dos últimos 60 s
_recentes: list[int] = []  # tokens das últimas chamadas, para estimar o custo de uma ação
_MAX_RECENTES = 20


def _limites() -> dict:
    cfg = carregar_configuracao()
    return {k: int(cfg.get(f"limite_{k}") or 0) for k in ("rpm", "tpm", "rpd")}


def _podar(agora: float):
    _eventos[:] = [e for e in _eventos if agora - e[0] < JANELA_S]


def _rpd_usado() -> int:
    try:
        with open(_CAMINHO, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if dados.get("data") == date.today().isoformat():
            return int(dados.get("rpd", 0))
    except Exception:
        pass
    return 0


def _segundos_ate_meia_noite() -> int:
    agora = datetime.now()
    amanha = datetime.combine(agora.date() + timedelta(days=1), datetime.min.time())
    return int((amanha - agora).total_seconds())


def _texto(obj) -> str:
    if isinstance(obj, (list, tuple)):
        return "".join(_texto_da_mensagem(m) for m in obj)
    return _texto_da_mensagem(obj)


def registrar(prompt, resp):
    # Nunca pode quebrar o jogo: qualquer erro de contagem é ignorado.
    try:
        uso = _usage(resp)
        tokens = int(uso.get("input_tokens") or 0) + int(uso.get("output_tokens") or 0)
        if not tokens:
            chars = len(_texto(prompt)) + len(_texto(resp))
            tokens = round(chars / CHARS_POR_TOKEN_PADRAO)
        with _LOCK:
            agora = time.time()
            _podar(agora)
            _eventos.append((agora, tokens))
            _recentes.append(tokens)
            del _recentes[:-_MAX_RECENTES]
            salvar_json(_CAMINHO, {"data": date.today().isoformat(), "rpd": _rpd_usado() + 1})
    except Exception:
        pass


def estado() -> dict:
    lim = _limites()
    with _LOCK:
        agora = time.time()
        _podar(agora)
        ev = list(_eventos)
        rpd = _rpd_usado()
    restante = lambda ts: max(0, int(ts + JANELA_S - agora + 0.999))
    zera = restante(ev[-1][0]) if ev else 0
    libera = restante(ev[0][0]) if ev else 0
    return {
        "rpm": {"limite": lim["rpm"], "usado": len(ev), "zera_em": zera, "libera_em": libera},
        "tpm": {"limite": lim["tpm"], "usado": sum(t for _, t in ev), "zera_em": zera, "libera_em": libera},
        "rpd": {"limite": lim["rpd"], "usado": rpd, "zera_em": _segundos_ate_meia_noite(), "libera_em": _segundos_ate_meia_noite()},
    }


def _fmt(seg: int) -> str:
    if seg >= 3600:
        return f"{seg // 3600}h {seg % 3600 // 60}min"
    return f"{seg // 60}min {seg % 60}s" if seg >= 60 else f"{seg}s"


def verificar(chamadas: int) -> str | None:
    # Devolve a mensagem de recusa se a ação (com `chamadas` requisições) não couber, ou None se couber.
    if chamadas <= 0:
        return None
    lim = _limites()
    with _LOCK:
        agora = time.time()
        _podar(agora)
        ev = list(_eventos)
        rpd = _rpd_usado()
        media = round(sum(_recentes) / len(_recentes)) if _recentes else 0

    if lim["rpd"] and rpd + chamadas > lim["rpd"]:
        return (f"Limite diário (RPD {rpd}/{lim['rpd']}): esta ação precisa de ~{chamadas} chamadas. "
                f"Reinicia à meia-noite (em {_fmt(_segundos_ate_meia_noite())}).")

    if lim["rpm"]:
        if chamadas > lim["rpm"]:
            return f"Esta ação precisa de ~{chamadas} chamadas, mais que o RPM configurado ({lim['rpm']}). Aumente o limite ou reduza os alvos."
        sobra = len(ev) + chamadas - lim["rpm"]
        if sobra > 0:
            espera = int(ev[sobra - 1][0] + JANELA_S - agora + 0.999)
            return f"Limite de RPM ({len(ev)}/{lim['rpm']}): esta ação precisa de ~{chamadas} chamadas. Aguarde {_fmt(espera)}."

    if lim["tpm"] and media:
        previsto = media * chamadas
        if previsto > lim["tpm"]:
            return f"Esta ação deve usar ~{previsto} tokens, mais que o TPM configurado ({lim['tpm']})."
        usado = sum(t for _, t in ev)
        if usado + previsto > lim["tpm"]:
            for i, (ts, t) in enumerate(ev):
                usado -= t
                if usado + previsto <= lim["tpm"]:
                    espera = int(ts + JANELA_S - agora + 0.999)
                    return f"Limite de TPM: esta ação deve usar ~{previsto} tokens. Aguarde {_fmt(espera)}."
    return None
