# Previsão de tokens de uma chamada à LLM antes de enviá-la (para a fila checar RPM/TPM).
# Mede o prompt de verdade (ele é montado localmente) e converte caracteres em tokens pela
# razão calibrada do personagem (metricas.json); a margem cobre a resposta e os prompts internos.
import os

from rpg.agentes import montar_prompt
from rpg.config import carregar_configuracao
from rpg.fichas import carregar_arquivo
from rpg.memoria import _arquivos_numerados, _caminho_temp, obter_pasta_agente
from rpg.metricas import CHARS_POR_TOKEN_PADRAO, _texto_da_mensagem, carregar_metricas

MARGEM_TOKENS = 2000  # resposta do agente + instruções internas
TOKENS_IMAGEM = 1500  # custo fixo estimado de uma imagem de contexto
CHARS_PROMPT_HISTORIADOR = 1500  # instruções fixas do historiador


def _razao(agente: str) -> float:
    dados = carregar_metricas(agente)
    if dados.get("provedor") != carregar_configuracao().get("provedor", ""):
        return CHARS_POR_TOKEN_PADRAO
    return float(dados.get("chars_por_token") or CHARS_POR_TOKEN_PADRAO)


def _tokens(agente: str, chars: int) -> int:
    return round(chars / _razao(agente))


def prever_entrada(agente: str, instrucao: str, historico: list, caminho_imagem: str | None = None) -> int:
    # Tokens previstos de uma resposta do jogador: prompt real (base, regras, memória, ficha, histórico,
    # instrução) + margem. Sem imagem no cálculo de caracteres: ela entra como custo fixo.
    mensagens = montar_prompt(agente, historico, instrucao, None)
    chars = sum(len(_texto_da_mensagem(m)) for m in mensagens)
    previsto = _tokens(agente, chars) + MARGEM_TOKENS
    return previsto + (TOKENS_IMAGEM if caminho_imagem else 0)


def _chars_arquivos(agente: str, prefixo: str) -> int:
    pasta = obter_pasta_agente(agente)
    return sum(len(carregar_arquivo(os.path.join(pasta, f))) for f in _arquivos_numerados(pasta, prefixo))


def prever_etapa(agente: str, etapa: str) -> int:
    # Tokens previstos de uma chamada do historiador: "rodada" (resumo da rodada), "cena" (todas as
    # rodadas viram uma cena) ou "mesa" (todas as cenas entram no mesa.txt).
    if etapa == "rodada":
        chars = CHARS_PROMPT_HISTORIADOR + len(carregar_arquivo(_caminho_temp(agente)))
    elif etapa == "cena":
        chars = CHARS_PROMPT_HISTORIADOR + _chars_arquivos(agente, "rodada")
    else:
        chars = CHARS_PROMPT_HISTORIADOR + _chars_arquivos(agente, "cena")
    return _tokens(agente, chars) + MARGEM_TOKENS

