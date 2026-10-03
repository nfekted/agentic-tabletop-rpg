import re
import unicodedata
from typing import Dict, Optional


def extrair_tags_resposta(texto: str) -> Dict[str, Optional[str]]:
    # Extrai o conteúdo de [pensamento], [fala], [acao], [duvida] e [chamar].
    if not texto:
        return {"pensamento": None, "fala": None, "acao": None, "duvida": None, "chamar": None}

    padroes = {
        "pensamento": r"\[pensamento\](.*?)\[/pensamento\]",
        "fala": r"\[fala\](.*?)\[/fala\]",
        "acao": r"\[acao\](.*?)\[/acao\]",
        "duvida": r"\[duvida\](.*?)\[/duvida\]",
        "chamar": r"\[chamar\](.*?)\[/chamar\]",
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
            r"\[(pensamento|fala|acao|duvida|chamar)\](.*?)(?=\[(?:pensamento|fala|acao|duvida|chamar|/)|$)",
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
    if tags.get("chamar"):
        partes.append(f'[chamar]{tags["chamar"]}[/chamar]')
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
    if tags.get("chamar"):
        partes.append(f'[chamar]{tags["chamar"]}[/chamar]')
    return " ".join(partes).strip()


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
