# Tokens: inimigos, NPCs e itens
import os
import re
from rpg.fichas import carregar_arquivo, salvar_arquivo
from rpg.paths import TOKENS as PASTA_TOKENS

CATEGORIAS = {
    "inimigo": "Inimigo",
    "npc": "NPC",
    "item": "Item",
}

EXEMPLO_PADRAO = ("default.txt", "Pode apagar ou modificar após ter 1 ficha")


def garantir_estrutura_tokens():
    for cat in CATEGORIAS:
        pasta_cat = os.path.join(PASTA_TOKENS, cat)
        os.makedirs(pasta_cat, exist_ok=True)
        if not any(f.endswith(".txt") for f in os.listdir(pasta_cat)):
            salvar_token(cat, *EXEMPLO_PADRAO)


def caminho_categoria(categoria: str) -> str:
    return os.path.join(PASTA_TOKENS, categoria)


def caminho_token(categoria: str, nome_arquivo: str) -> str:
    return os.path.join(PASTA_TOKENS, categoria, nome_arquivo)


def listar_tokens(categoria: str) -> list[str]:
    pasta = caminho_categoria(categoria)
    os.makedirs(pasta, exist_ok=True)
    return sorted(f for f in os.listdir(pasta) if f.endswith(".txt") and not f.startswith("."))


def carregar_token(categoria: str, nome_arquivo: str) -> str:
    return carregar_arquivo(caminho_token(categoria, nome_arquivo))


def salvar_token(categoria: str, nome_arquivo: str, conteudo: str):
    salvar_arquivo(caminho_token(categoria, nome_arquivo), conteudo)


def criar_token(categoria: str, nome: str, conteudo_inicial: str = "") -> str | None:
    nome = nome.strip()
    if not nome:
        return None

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


def extensao_imagem(nome_upload: str, padrao: str) -> str:
    ext = os.path.splitext(os.path.basename(nome_upload or ""))[1].lower()
    return ext if ext in EXTENSOES_IMAGEM else padrao


def caminho_imagem_token(categoria: str, nome_arquivo: str) -> str | None:
    # a imagem fica ao lado do .txt, com o mesmo nome (goblin.txt -> goblin.png)
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
    caminho = os.path.splitext(caminho_token(categoria, nome_arquivo))[0] + extensao_imagem(nome_upload, ".png")
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
