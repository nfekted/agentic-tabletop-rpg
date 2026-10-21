# Resumo de combate: marca [INICIO COMBATE] na memória da rodada e troca do que vem depois dela por um resumo.
import os
import re
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from rpg.config import obter_llm
from rpg.limites import invocar
from rpg.memoria import (
    GerenciadorMemoriaRPG, _caminho_temp, _ler, limpar_tags, tags_para_texto, texto_resposta,
)

MARCA_COMBATE = "[INICIO COMBATE]"
PREFIXO_RESUMO = "Resumo do combate"

# linha de pensamento solto do autor ("Fulano (pensamento): [pensamento]...[/pensamento]")
_RE_LINHA_PENSAMENTO = re.compile(r"^\S+ \(pensamento\):[ \t]*\[pensamento\].*?\[/pensamento\][ \t]*\n?", re.DOTALL | re.MULTILINE | re.IGNORECASE)
_RE_TAG_PENSAMENTO = re.compile(r"\[pensamento\].*?\[/pensamento\][ \t]*", re.DOTALL | re.IGNORECASE)
_RE_SO_NOME = re.compile(r"^\S+( \([^)]*\))?:\s*$")  # "Fulano:" ou "Mestre (para A, B):" sem conteúdo


def marcar_inicio(agentes: List[str]):
    GerenciadorMemoriaRPG.salvar_log_rodada_atual(MARCA_COMBATE, agentes)


def _trecho_apos_marca(texto: str) -> str | None:
    i = texto.rfind(MARCA_COMBATE)
    return None if i < 0 else texto[i + len(MARCA_COMBATE):].lstrip("\n")


def normalizar(trecho: str) -> str:
    # Só o que é público: tira os pensamentos do autor, para que todos os presentes fiquem com o mesmo texto.
    trecho = _RE_LINHA_PENSAMENTO.sub("", trecho)
    trecho = _RE_TAG_PENSAMENTO.sub("", trecho)
    linhas = [l.rstrip() for l in trecho.split("\n")]
    return "\n".join(l for l in linhas if l.strip() and not _RE_SO_NOME.match(l))


def trecho_normalizado(agente: str) -> str | None:
    caminho = _caminho_temp(agente)
    if not os.path.exists(caminho):
        return None
    trecho = _trecho_apos_marca(_ler(caminho))
    return None if trecho is None else normalizar(trecho)


def trechos_por_grupo(agentes: List[str]) -> List[dict]:
    # Quem tem exatamente o mesmo trecho público forma um grupo (conversa privada gera outro grupo).
    grupos: dict[str, List[str]] = {}
    for ag in agentes:
        texto = trecho_normalizado(ag)
        if texto is not None:
            grupos.setdefault(texto, []).append(ag)
    return [{"agentes": ags, "texto": t, "chars": len(t)} for t, ags in grupos.items()]


def aplicar_resumo(agentes: List[str], resumo: str):
    # Troca tudo depois da última marca pelo resumo e recoloca a marca depois dele (o resumo fica "congelado").
    resumo = resumo.strip()
    for ag in agentes:
        caminho = _caminho_temp(ag)
        if not os.path.exists(caminho):
            continue
        texto = _ler(caminho)
        i = texto.rfind(MARCA_COMBATE)
        if i < 0:
            continue
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"{texto[:i]}{PREFIXO_RESUMO}: {resumo}\n{MARCA_COMBATE}\n")


def remover_marca(agentes: List[str]):
    for ag in agentes:
        caminho = _caminho_temp(ag)
        if not os.path.exists(caminho):
            continue
        texto = _ler(caminho)
        if MARCA_COMBATE not in texto:
            continue
        linhas = [l for l in texto.split("\n") if l.strip() != MARCA_COMBATE]
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))


def sugerir_resumo(texto: str) -> str:
    # Uma chamada ao historiador: o mestre revisa o resultado antes de aplicar.
    prompt_base = """Você é o Cronista de uma mesa de RPG cooperativo e vai resumir um COMBATE.
Muitas ações se repetem (golpes que erram, esquivas, curas pequenas) e não precisam ser lembradas.

## MANTENHA
- Quem foi derrotado, morto, capturado ou fugiu.
- Danos permanentes, condições graves e mudanças de estado de personagens (ferimentos graves, insanidade).
- Itens, habilidades ou recursos importantes usados ou perdidos.
- Mudanças de posição ou de situação que afetam o que vem depois (quem está onde, o que sobrou).
- Decisões táticas e falas que revelem algo importante.

## DESCARTE
- Sequências de ataques, esquivas e tentativas sem consequência: resuma em uma frase ("trocaram golpes por vários turnos").

## FORMATO
Prosa corrida em terceira pessoa, em até 2 parágrafos curtos. Use os nomes próprios. Não use tags, listas nem títulos. Não invente nada."""
    mensagens = [
        SystemMessage(content=prompt_base),
        HumanMessage(content=f"## REGISTRO DO COMBATE\n{tags_para_texto(texto)}\n\nRESUMO DO COMBATE:"),
    ]
    return limpar_tags(texto_resposta(invocar(obter_llm(temperature=0.3), mensagens)))
