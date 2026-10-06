import os
import base64
import tempfile
import uuid

from rpg.memoria import obter_pasta_agente
from rpg.tokens_manager import EXTENSOES_IMAGEM, extensao_imagem


def salvar_imagem_upload(nome_arquivo: str, conteudo: bytes) -> str:
    # salva em um caminho temporário e devolve o caminho
    if not conteudo:
        return None

    pasta_tmp = os.path.join(tempfile.gettempdir(), "rpg_agent_uploads")
    os.makedirs(pasta_tmp, exist_ok=True)
    caminho = os.path.join(pasta_tmp, f"upload_{uuid.uuid4().hex}{extensao_imagem(nome_arquivo, '.jpg')}")
    with open(caminho, "wb") as f:
        f.write(conteudo)
    return caminho


def caminho_avatar(agente: str) -> str:
    pasta = obter_pasta_agente(agente)
    for ext in EXTENSOES_IMAGEM:
        caminho = os.path.join(pasta, f"avatar{ext}")
        if os.path.exists(caminho):
            return caminho
    return None


def salvar_avatar_jogador(agente: str, nome_arquivo: str, conteudo: bytes) -> str:
    if not conteudo:
        return None

    remover_avatar_jogador(agente)
    caminho = os.path.join(obter_pasta_agente(agente), f"avatar{extensao_imagem(nome_arquivo, '.png')}")
    with open(caminho, "wb") as f:
        f.write(conteudo)
    return caminho


def remover_avatar_jogador(agente: str):
    caminho = caminho_avatar(agente)
    while caminho:
        os.remove(caminho)
        caminho = caminho_avatar(agente)


def carregar_imagem_base64(caminho_imagem: str) -> str:
    with open(caminho_imagem, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def obter_mimetype_imagem(caminho_imagem: str) -> str:
    extensao = os.path.splitext(caminho_imagem)[1].lower()
    mapa_mimetypes = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    return mapa_mimetypes.get(extensao, "image/jpeg")
