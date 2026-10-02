# Decide quando oferecer a compressão de memória (antes: ui/compressao_panel.verificar_compressoes).
from rpg.config import carregar_agentes
from rpg.metricas import calcular_contexto
from services.sessao import obter, salvar

# Abaixo disso, o peso do contexto não está na memória (é regras/ficha/histórico): comprimir não ajuda.
LIMITE_MEMORIA_UTIL_PCT = 15


def proxima_pergunta() -> dict | None:
    # Devolve no máximo um personagem por chamada e o marca como "perguntado" para a
    # medição atual — uma nova medição (nova chamada de LLM) volta a perguntar.
    perguntadas = obter()["compressao_perguntada"]
    for nome in carregar_agentes():
        ctx = calcular_contexto(nome)
        if not ctx or not ctx["passou_gatilho"]:
            continue
        if perguntadas.get(nome) == ctx["medicao_id"]:
            continue
        perguntadas[nome] = ctx["medicao_id"]
        salvar()
        memoria_tokens = ctx["partes"].get("memoria", 0)
        return {
            "agente": nome,
            "memoria_util": memoria_tokens / ctx["limite"] * 100 >= LIMITE_MEMORIA_UTIL_PCT,
        }
    return None
