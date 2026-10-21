# Linhas do histórico da cena com audiência: "@[A|B] Autor: texto" só é lido por A e B; sem o prefixo, é pública.
import re

_PREFIXO = re.compile(r"^@\[([^\]]*)\] ")


def com_audiencia(linha: str, ouvintes: list[str], todos: list[str]) -> str:
    # Só marca quando alguém da mesa fica de fora.
    if set(todos) <= set(ouvintes):
        return linha
    return f"@[{'|'.join(ouvintes)}] {linha}"


def separar(linha: str) -> tuple[list[str] | None, str]:
    # (ouvintes ou None se pública, texto sem o prefixo)
    m = _PREFIXO.match(linha)
    if not m:
        return None, linha
    return m.group(1).split("|"), linha[m.end():]


def visivel_para(linhas: list[str], agente: str) -> list[str]:
    # O que o jogador lê no prompt: linhas públicas e as dos grupos de que faz parte, sem o prefixo.
    saida = []
    for linha in linhas:
        ouvintes, texto = separar(linha)
        if ouvintes is None or agente in ouvintes:
            saida.append(texto)
    return saida
