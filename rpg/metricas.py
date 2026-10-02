# Métricas de contexto por personagem (tokens do último prompt, calibração chars/token)
# gravadas em arquivos/memoria_<agente>/metricas.json
import json
import os
from datetime import datetime

from rpg.config import carregar_configuracao
from rpg.paths import ARQUIVOS

CHARS_POR_TOKEN_PADRAO = 3.0
_PARTES = ("base", "regras", "memoria", "ficha", "turno")  # ordem das mensagens em montar_prompt


def caminho_metricas(agente: str) -> str:
    return os.path.join(ARQUIVOS, f"memoria_{agente}", "metricas.json")


def carregar_metricas(agente: str) -> dict:
    try:
        with open(caminho_metricas(agente), "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
    except Exception:
        return {}


def _salvar_metricas(agente: str, dados: dict):
    caminho = caminho_metricas(agente)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def _texto_da_mensagem(msg) -> str:
    conteudo = getattr(msg, "content", msg)
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):  # multimodal: só conta o texto (imagem é tratada à parte)
        return "".join(p.get("text", "") for p in conteudo if isinstance(p, dict))
    return str(conteudo)


def _medir_partes(mensagens) -> dict:
    return {nome: len(_texto_da_mensagem(m)) for nome, m in zip(_PARTES, mensagens)}


def _usage(resp) -> dict:
    uso = getattr(resp, "usage_metadata", None)
    return uso if isinstance(uso, dict) else {}


def registrar_chamada(agente: str, mensagens, resp, provedor: str, com_imagem: bool = False):
    # Nunca pode quebrar o jogo: qualquer erro de métrica é ignorado.
    try:
        antigo = carregar_metricas(agente)
        partes = _medir_partes(mensagens)
        chars = sum(partes.values())

        razao = antigo.get("chars_por_token", CHARS_POR_TOKEN_PADRAO)
        if antigo.get("provedor") != provedor:
            razao = CHARS_POR_TOKEN_PADRAO

        uso = _usage(resp)
        tokens_in = uso.get("input_tokens")
        detalhes = uso.get("input_token_details") or {}
        estimado = not tokens_in

        if tokens_in:
            if not com_imagem and chars:
                nova = max(1.5, min(6.0, chars / tokens_in))
                razao = round(0.7 * razao + 0.3 * nova, 3)
        else:
            tokens_in = round(chars / razao)

        dados = {
            "provedor": provedor,
            "medicao_id": int(antigo.get("medicao_id", 0)) + 1,
            "atualizado_em": datetime.now().isoformat(timespec="seconds"),
            "tokens_entrada_ultimo": int(tokens_in),
            "tokens_saida_ultimo": int(uso.get("output_tokens") or 0),
            "tokens_cache_ultimo": int(detalhes.get("cache_read") or 0),
            "chars_enviados_ultimo": chars,
            "chars_por_token": razao,
            "com_imagem": bool(com_imagem),
            "estimado": estimado,
            "partes": partes,
        }
        _salvar_metricas(agente, dados)
        dados["contexto"] = calcular_contexto(agente)
        _salvar_metricas(agente, dados)
    except Exception:
        pass


def calcular_contexto(agente: str):
    # Devolve None se o controle está desligado (limite 0) ou se ainda não há medição.
    cfg = carregar_configuracao()
    limite = int(cfg.get("limite_contexto_tokens") or 0)
    dados = carregar_metricas(agente)
    if limite <= 0 or not dados.get("tokens_entrada_ultimo"):
        return None

    usado = int(dados["tokens_entrada_ultimo"])
    pct = usado / limite * 100
    gatilho = int(cfg.get("gatilho_compressao_pct") or 85)
    razao = dados.get("chars_por_token") or CHARS_POR_TOKEN_PADRAO
    partes_tokens = {k: round(v / razao) for k, v in (dados.get("partes") or {}).items()}

    if pct >= gatilho:
        faixa = "vermelho"
    elif pct >= 60:
        faixa = "ambar"
    else:
        faixa = "verde"

    return {
        "usado": usado,
        "limite": limite,
        "pct": round(pct, 1),
        "gatilho_pct": gatilho,
        "passou_gatilho": pct >= gatilho,
        "faixa": faixa,
        "partes": partes_tokens,
        "estimado": bool(dados.get("estimado")),
        "medicao_id": int(dados.get("medicao_id", 0)),
        "atualizado_em": dados.get("atualizado_em", ""),
    }


def atualizar_apos_compressao(agente: str, chars_antes: int, chars_depois: int):
    # Ajusta a última medição pela memória removida, para a barra cair sem esperar nova chamada.
    try:
        dados = carregar_metricas(agente)
        if not dados.get("tokens_entrada_ultimo"):
            return
        razao = dados.get("chars_por_token") or CHARS_POR_TOKEN_PADRAO
        delta = round((chars_antes - chars_depois) / razao)
        dados["tokens_entrada_ultimo"] = max(0, int(dados["tokens_entrada_ultimo"]) - delta)
        if dados.get("partes"):
            dados["partes"]["memoria"] = max(0, dados["partes"].get("memoria", 0) - (chars_antes - chars_depois))
        dados["estimado"] = True
        dados["medicao_id"] = int(dados.get("medicao_id", 0)) + 1
        dados["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
        _salvar_metricas(agente, dados)
        dados["contexto"] = calcular_contexto(agente)
        _salvar_metricas(agente, dados)
    except Exception:
        pass
