import re
import unicodedata
from typing import Dict, Optional


_TAGS = ("pensamento", "fala", "acao", "duvida", "chamar")


def extrair_tags_resposta(texto: str) -> Dict[str, Optional[str]]:
    if not texto:
        return dict.fromkeys(_TAGS)

    resultado: Dict[str, Optional[str]] = {}
    for tag in _TAGS:
        m = re.search(rf"\[{tag}\](.*?)\[/{tag}\]", texto, re.DOTALL | re.IGNORECASE)
        resultado[tag] = (m.group(1).strip() or None) if m else None

    # sem tag fechada: aceita "[tag] texto" até a próxima tag ou o fim
    if not any(resultado.values()):
        nomes = "|".join(_TAGS)
        partes = re.findall(rf"\[({nomes})\](.*?)(?=\[(?:{nomes}|/)|$)", texto, re.DOTALL | re.IGNORECASE)
        for t, c in partes:
            c_strip = c.strip()
            if c_strip:
                resultado[t.lower()] = c_strip

    # texto puro, sem tags, é fala
    if not any(resultado.values()) and texto.strip():
        resultado["fala"] = texto.strip()

    return resultado


def _formatar(tags: Dict[str, Optional[str]], nomes: tuple) -> str:
    return " ".join(f"[{t}]{tags[t]}[/{t}]" for t in nomes if tags.get(t)).strip()


def formatar_conteudo_publico(tags: Dict[str, Optional[str]]) -> str:
    # o que os outros personagens podem ouvir/ver (sem o pensamento)
    return _formatar(tags, _TAGS[1:])


def formatar_para_autor(tags: Dict[str, Optional[str]]) -> str:
    return _formatar(tags, _TAGS)


def _normalizar_nome(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFD", nome)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold().strip()


def separar_chamada(texto: str, nomes: list) -> Optional[tuple]:
    # "NomeExato: mensagem" -> (nome canônico, mensagem). Nome fora da lista ou sem mensagem: None.
    m = re.match(r"\s*([^:]+?)\s*:\s*(.+)", texto or "", re.DOTALL)
    if not m:
        return None
    alvo = _normalizar_nome(m.group(1))
    for nome in nomes:
        if _normalizar_nome(nome) == alvo:
            return nome, m.group(2).strip()
    return None


def apenas_pensamento(tags: Dict[str, Optional[str]]) -> bool:
    return bool(tags.get("pensamento")) and not (
        tags.get("fala") or tags.get("acao") or tags.get("duvida") or tags.get("chamar")
    )
