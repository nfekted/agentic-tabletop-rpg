# Contadores de RPM / TPM / RPD das chamadas à LLM (limites opcionais; 0 = desligado).
# O minuto é uma janela deslizante de 60 s. Cada chamada vira um evento em arquivos/limites.json
# (hora do envio, hora em que sai da janela e tokens), então o uso sobrevive a reiniciar a API.
# O RPD é um contador do dia, salvo no mesmo arquivo com a data.
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from rpg.config import carregar_configuracao
from rpg.fichas import salvar_json
from rpg.metricas import CHARS_POR_TOKEN_PADRAO, _texto_da_mensagem, _usage
from rpg.paths import ARQUIVOS

JANELA_S = 60
FOLGA_S = 5  # segundos a mais ao esperar a janela liberar (relógios do provedor e local não batem)
_CAMINHO = os.path.join(ARQUIVOS, "limites.json")
_LOCK = threading.RLock()
_recentes: list[int] = []  # tokens das últimas chamadas, para estimar o custo de uma ação
_MAX_RECENTES = 20

_agora = time.time  # trocável nos testes
ouvintes: list = []  # callbacks sem argumentos, chamados quando o uso muda (a API publica o evento SSE)


@dataclass
class Bloqueio:
    # tipo "espera": cabe depois de `segundos`; "pausa": não adianta esperar (RPD ou pedido maior que o limite)
    tipo: str
    segundos: int
    mensagem: str


def _limites() -> dict:
    cfg = carregar_configuracao()
    return {k: int(cfg.get(f"limite_{k}") or 0) for k in ("rpm", "tpm", "rpd")}


def _avisar():
    for f in list(ouvintes):
        try:
            f()
        except Exception:
            pass


def _carregar() -> dict:
    try:
        with open(_CAMINHO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    if dados.get("data") != date.today().isoformat():
        dados["data"] = date.today().isoformat()
        dados["rpd"] = 0
    dados["rpd"] = int(dados.get("rpd") or 0)
    eventos = dados.get("eventos")
    dados["eventos"] = [e for e in eventos if isinstance(e, dict)] if isinstance(eventos, list) else []
    return dados


def _gravar(dados: dict):
    try:
        salvar_json(_CAMINHO, dados)
    except Exception:
        pass


def _carregar_podado(agora: float) -> dict:
    # Lê o arquivo e descarta os eventos que já saíram da janela (regrava só se algo expirou).
    dados = _carregar()
    vivos = [e for e in dados["eventos"] if float(e.get("libera_em", 0)) > agora]
    if len(vivos) != len(dados["eventos"]):
        dados["eventos"] = vivos
        _gravar(dados)
    dados["eventos"] = sorted(vivos, key=lambda e: e["libera_em"])
    return dados


def _segundos_ate_meia_noite() -> int:
    agora = datetime.now()
    amanha = datetime.combine(agora.date() + timedelta(days=1), datetime.min.time())
    return int((amanha - agora).total_seconds())


def _texto(obj) -> str:
    if isinstance(obj, (list, tuple)):
        return "".join(_texto_da_mensagem(m) for m in obj)
    return _texto_da_mensagem(obj)


def _tokens_da_resposta(prompt, resp) -> int:
    uso = _usage(resp)
    tokens = int(uso.get("input_tokens") or 0) + int(uso.get("output_tokens") or 0)
    if not tokens:
        tokens = round((len(_texto(prompt)) + len(_texto(resp))) / CHARS_POR_TOKEN_PADRAO)
    return tokens


def reservar(tokens_previstos: int) -> str:
    # Conta a chamada no momento do envio (como o provedor), com os tokens previstos até a resposta chegar.
    with _LOCK:
        agora = _agora()
        dados = _carregar_podado(agora)
        id_ = uuid.uuid4().hex[:10]
        dados["eventos"].append({
            "id": id_, "ts": round(agora, 3), "libera_em": round(agora + JANELA_S, 3),
            "tokens": max(0, int(tokens_previstos)), "previsto": True,
        })
        dados["rpd"] += 1
        _gravar(dados)
    _avisar()
    return id_


def confirmar(id_: str, prompt, resp):
    # Troca a previsão pelo consumo real. Nunca pode quebrar o jogo: qualquer erro de contagem é ignorado.
    try:
        tokens = _tokens_da_resposta(prompt, resp)
        with _LOCK:
            dados = _carregar_podado(_agora())
            for e in dados["eventos"]:
                if e.get("id") == id_:
                    e["tokens"] = tokens
                    e["previsto"] = False
                    break
            _gravar(dados)
            _recentes.append(tokens)
            del _recentes[:-_MAX_RECENTES]
    except Exception:
        pass
    _avisar()


def invocar(llm, prompt, tokens_previstos: int | None = None):
    # llm.invoke contabilizado: reserva no envio e confirma com o usage_metadata. Se o provedor falhar,
    # a reserva fica (muitos provedores contam a requisição mesmo com erro 429/503).
    if tokens_previstos is None:
        tokens_previstos = round(len(_texto(prompt)) / CHARS_POR_TOKEN_PADRAO)
    id_ = reservar(tokens_previstos)
    resp = llm.invoke(prompt)
    confirmar(id_, prompt, resp)
    return resp


def estado() -> dict:
    lim = _limites()
    with _LOCK:
        agora = _agora()
        dados = _carregar_podado(agora)
    ev = dados["eventos"]
    restante = lambda ts: max(0, int(ts - agora + 0.999))
    zera = restante(ev[-1]["libera_em"]) if ev else 0
    libera = restante(ev[0]["libera_em"]) if ev else 0
    meia_noite = _segundos_ate_meia_noite()
    return {
        "rpm": {"limite": lim["rpm"], "usado": len(ev), "zera_em": zera, "libera_em": libera},
        "tpm": {"limite": lim["tpm"], "usado": sum(int(e["tokens"]) for e in ev), "zera_em": zera, "libera_em": libera},
        "rpd": {"limite": lim["rpd"], "usado": dados["rpd"], "zera_em": meia_noite, "libera_em": meia_noite},
    }


def _fmt(seg: int) -> str:
    if seg >= 3600:
        return f"{seg // 3600}h {seg % 3600 // 60}min"
    return f"{seg // 60}min {seg % 60}s" if seg >= 60 else f"{seg}s"


def controle_ativo() -> bool:
    # A fila só verifica/espera quando RPM e TPM estão preenchidos.
    lim = _limites()
    return lim["rpm"] > 0 and lim["tpm"] > 0


def espera_necessaria(tokens_previstos: int) -> Bloqueio | None:
    # None se a próxima chamada (com `tokens_previstos` de entrada + saída) cabe agora.
    lim = _limites()
    with _LOCK:
        agora = _agora()
        dados = _carregar_podado(agora)
    ev = dados["eventos"]

    if lim["rpd"] and dados["rpd"] + 1 > lim["rpd"]:
        return Bloqueio(
            "pausa", _segundos_ate_meia_noite(),
            f"Limite diário atingido (RPD {dados['rpd']}/{lim['rpd']}). Reinicia à meia-noite "
            f"(em {_fmt(_segundos_ate_meia_noite())}); continue a fila depois.",
        )

    if lim["tpm"] and tokens_previstos > lim["tpm"]:
        return Bloqueio(
            "pausa", 0,
            f"Esta chamada deve usar ~{tokens_previstos} tokens, mais que o TPM configurado ({lim['tpm']}). "
            "Aumente o limite ou reduza a memória/ficha.",
        )

    def cabe(restantes: list) -> bool:
        if lim["rpm"] and len(restantes) + 1 > lim["rpm"]:
            return False
        if lim["tpm"] and sum(int(e["tokens"]) for e in restantes) + tokens_previstos > lim["tpm"]:
            return False
        return True

    if cabe(ev):
        return None
    # ev está ordenado por libera_em: tira os eventos que expiram primeiro até caber
    for i, e in enumerate(ev):
        if cabe(ev[i + 1:]):
            espera = max(1, int(e["libera_em"] - agora + 0.999))
            return Bloqueio(
                "espera", espera + FOLGA_S,
                f"Aguardando liberar o limite de RPM/TPM (~{_fmt(espera + FOLGA_S)}).",
            )
    return Bloqueio("pausa", 0, "Não há como encaixar esta chamada nos limites de RPM/TPM configurados.")


def verificar(chamadas: int) -> str | None:
    # Devolve a mensagem de recusa se a ação (com `chamadas` requisições) não couber, ou None se couber.
    # Usado pelas ações que ainda não passam pela fila (ex.: compressão manual da memória).
    if chamadas <= 0:
        return None
    lim = _limites()
    with _LOCK:
        agora = _agora()
        dados = _carregar_podado(agora)
        media = round(sum(_recentes) / len(_recentes)) if _recentes else 0
    ev = dados["eventos"]
    rpd = dados["rpd"]

    if lim["rpd"] and rpd + chamadas > lim["rpd"]:
        return (f"Limite diário (RPD {rpd}/{lim['rpd']}): esta ação precisa de ~{chamadas} chamadas. "
                f"Reinicia à meia-noite (em {_fmt(_segundos_ate_meia_noite())}).")

    if lim["rpm"]:
        if chamadas > lim["rpm"]:
            return f"Esta ação precisa de ~{chamadas} chamadas, mais que o RPM configurado ({lim['rpm']}). Aumente o limite ou reduza os alvos."
        sobra = len(ev) + chamadas - lim["rpm"]
        if sobra > 0:
            espera = int(ev[sobra - 1]["libera_em"] - agora + 0.999)
            return f"Limite de RPM ({len(ev)}/{lim['rpm']}): esta ação precisa de ~{chamadas} chamadas. Aguarde {_fmt(espera)}."

    if lim["tpm"] and media:
        previsto = media * chamadas
        if previsto > lim["tpm"]:
            return f"Esta ação deve usar ~{previsto} tokens, mais que o TPM configurado ({lim['tpm']})."
        usado = sum(int(e["tokens"]) for e in ev)
        if usado + previsto > lim["tpm"]:
            for e in ev:
                usado -= int(e["tokens"])
                if usado + previsto <= lim["tpm"]:
                    espera = int(e["libera_em"] - agora + 0.999)
                    return f"Limite de TPM: esta ação deve usar ~{previsto} tokens. Aguarde {_fmt(espera)}."
    return None
