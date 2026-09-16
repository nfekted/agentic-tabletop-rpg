import re
from typing import Dict, Optional


def extrair_tags_resposta(texto: str) -> Dict[str, Optional[str]]:
    # Extrai o conteúdo de [pensamento], [fala], [acao] e [duvida].
    if not texto:
        return {"pensamento": None, "fala": None, "acao": None, "duvida": None}

    padroes = {
        "pensamento": r"\[pensamento\](.*?)\[/pensamento\]",
        "fala": r"\[fala\](.*?)\[/fala\]",
        "acao": r"\[acao\](.*?)\[/acao\]",
        "duvida": r"\[duvida\](.*?)\[/duvida\]",
    }

    resultado: Dict[str, Optional[str]] = {}
    for tag, regex in padroes.items():
        m = re.search(regex, texto, re.DOTALL | re.IGNORECASE)
        if m:
            conteudo = m.group(1).strip()
            resultado[tag] = conteudo if conteudo else None
        else:
            resultado[tag] = None

    # Fallback: Se nenhuma tag fechada foi capturada, busca padrão [tag] até próxima tag ou fim
    if not any(resultado.values()):
        partes = re.findall(
            r"\[(pensamento|fala|acao|duvida)\](.*?)(?=\[(?:pensamento|fala|acao|duvida|/)|$)",
            texto,
            re.DOTALL | re.IGNORECASE,
        )
        for t, c in partes:
            c_strip = c.strip()
            if c_strip:
                resultado[t.lower()] = c_strip

    # Fallback final: se o modelo respondeu texto puro sem tags
    if not any(resultado.values()) and texto.strip():
        # Trata texto puro como fala
        resultado["fala"] = texto.strip()

    return resultado


def formatar_conteudo_publico(tags: Dict[str, Optional[str]]) -> str:
    # Retorna apenas a parte pública da mensagem (o que outros personagens podem ouvir/ver).
    partes = []
    if tags.get("fala"):
        partes.append(f'[fala]{tags["fala"]}[/fala]')
    if tags.get("acao"):
        partes.append(f'[acao]{tags["acao"]}[/acao]')
    if tags.get("duvida"):
        partes.append(f'[duvida]{tags["duvida"]}[/duvida]')
    return " ".join(partes).strip()


def formatar_para_autor(tags: Dict[str, Optional[str]]) -> str:
    # Retorna o conjunto completo para o próprio autor (pensamento + fala + acao/duvida).
    partes = []
    if tags.get("pensamento"):
        partes.append(f'[pensamento]{tags["pensamento"]}[/pensamento]')
    if tags.get("fala"):
        partes.append(f'[fala]{tags["fala"]}[/fala]')
    if tags.get("acao"):
        partes.append(f'[acao]{tags["acao"]}[/acao]')
    if tags.get("duvida"):
        partes.append(f'[duvida]{tags["duvida"]}[/duvida]')
    return " ".join(partes).strip()


def formatar_exibicao_amigavel(tags: Dict[str, Optional[str]]) -> str:
    # Formata a resposta de forma limpa para exibição no chat/interface.
    partes = []
    if tags.get("fala"):
        partes.append(f'"{tags["fala"]}"')
    if tags.get("acao"):
        partes.append(f'*{tags["acao"]}*')
    if tags.get("duvida"):
        partes.append(f'*(Dúvida ao Mestre: {tags["duvida"]})*')
    return " ".join(partes).strip()


def tem_acao(tags: Dict[str, Optional[str]]) -> bool:
    return bool(tags.get("acao"))


def tem_duvida(tags: Dict[str, Optional[str]]) -> bool:
    return bool(tags.get("duvida"))


def tem_pensamento(tags: Dict[str, Optional[str]]) -> bool:
    return bool(tags.get("pensamento"))


def apenas_pensamento(tags: Dict[str, Optional[str]]) -> bool:
    return bool(tags.get("pensamento")) and not (
        tags.get("fala") or tags.get("acao") or tags.get("duvida")
    )

