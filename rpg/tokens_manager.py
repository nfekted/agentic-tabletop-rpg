# Gerenciador de arquivos e pastas para Inimigos, Itens e NPCs (Tokens)
import os
import re
from rpg.paths import TOKENS

PASTA_TOKENS = TOKENS

CATEGORIAS = {
    "inimigo": "Inimigo",
    "npc": "NPC",
    "item": "Item",
}

EXEMPLOS_PADRAO = {
    "inimigo": (
        "default.txt",
        ("Pode apagar ou modificar após ter 1 ficha"),
    ),
    "npc": (
        "default.txt",
        ("Pode apagar ou modificar após ter 1 ficha"),
    ),
    "item": (
        "default.txt",
        ("Pode apagar ou modificar após ter 1 ficha"),
    ),
}


def garantir_estrutura_tokens():
    # Garante que a pasta tokens e as subpastas inimigo, npc e item existam.
    for cat in CATEGORIAS:
        pasta_cat = os.path.join(PASTA_TOKENS, cat)
        os.makedirs(pasta_cat, exist_ok=True)

        # Se a pasta da categoria estiver vazia, cria o exemplo correspondente
        arquivos = [f for f in os.listdir(pasta_cat) if f.endswith(".txt")]
        if not arquivos and cat in EXEMPLOS_PADRAO:
            nome_exemplo, conteudo_exemplo = EXEMPLOS_PADRAO[cat]
            salvar_token(cat, nome_exemplo, conteudo_exemplo)


def caminho_categoria(categoria: str) -> str:
    return os.path.join(PASTA_TOKENS, categoria)


def caminho_token(categoria: str, nome_arquivo: str) -> str:
    return os.path.join(PASTA_TOKENS, categoria, nome_arquivo)


def listar_tokens(categoria: str) -> list[str]:
    pasta = caminho_categoria(categoria)
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    return sorted(
        [f for f in os.listdir(pasta) if f.endswith(".txt") and not f.startswith(".")]
    )


def carregar_token(categoria: str, nome_arquivo: str) -> str:
    caminho = caminho_token(categoria, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def salvar_token(categoria: str, nome_arquivo: str, conteudo: str):
    caminho = caminho_token(categoria, nome_arquivo)
    pasta = os.path.dirname(caminho)
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def criar_token(categoria: str, nome: str, conteudo_inicial: str = "") -> str | None:
    nome = nome.strip()
    if not nome:
        return None

    # Remove extensão se já digitada e normaliza slug
    if nome.lower().endswith(".txt"):
        nome = nome[:-4]

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome).strip("_").lower()
    if not slug:
        return None

    nome_arquivo = f"{slug}.txt"
    caminho = caminho_token(categoria, nome_arquivo)
    if os.path.exists(caminho):
        return None

    salvar_token(categoria, nome_arquivo, conteudo_inicial)
    return nome_arquivo


EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg", ".webp")


def caminho_imagem_token(categoria: str, nome_arquivo: str) -> str | None:
    # A imagem fica ao lado do .txt, com o mesmo nome: goblin.txt -> goblin.png
    base = os.path.splitext(caminho_token(categoria, nome_arquivo))[0]
    for ext in EXTENSOES_IMAGEM:
        if os.path.exists(base + ext):
            return base + ext
    return None


def remover_imagem_token(categoria: str, nome_arquivo: str):
    caminho = caminho_imagem_token(categoria, nome_arquivo)
    while caminho:
        os.remove(caminho)
        caminho = caminho_imagem_token(categoria, nome_arquivo)


def salvar_imagem_token(categoria: str, nome_arquivo: str, nome_upload: str, conteudo: bytes) -> str | None:
    if not conteudo:
        return None
    remover_imagem_token(categoria, nome_arquivo)
    ext = os.path.splitext(os.path.basename(nome_upload or ""))[1].lower()
    if ext not in EXTENSOES_IMAGEM:
        ext = ".png"
    caminho = os.path.splitext(caminho_token(categoria, nome_arquivo))[0] + ext
    with open(caminho, "wb") as f:
        f.write(conteudo)
    return caminho


def excluir_token(categoria: str, nome_arquivo: str) -> bool:
    caminho = caminho_token(categoria, nome_arquivo)
    if os.path.exists(caminho):
        remover_imagem_token(categoria, nome_arquivo)
        os.remove(caminho)
        return True
    return False
