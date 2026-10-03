import os
import base64
import tempfile
import uuid

from rpg.memoria import obter_pasta_agente

_EXTENSOES_AVATAR = (".png", ".jpg", ".jpeg", ".webp")


def salvar_imagem_upload(nome_arquivo: str, conteudo: bytes) -> str:
    # Salva uma imagem enviada (nome + bytes) em um caminho temporário e retorna o caminho
    if not conteudo:
        return None

    extensao = os.path.splitext(os.path.basename(nome_arquivo or ""))[1].lower()
    if extensao not in _EXTENSOES_AVATAR:
        extensao = ".jpg"
    pasta_tmp = os.path.join(tempfile.gettempdir(), "rpg_agent_uploads")
    os.makedirs(pasta_tmp, exist_ok=True)
    caminho = os.path.join(pasta_tmp, f"upload_{uuid.uuid4().hex}{extensao}")

    with open(caminho, "wb") as f:
        f.write(conteudo)

    return caminho


def caminho_avatar(agente: str) -> str:
    # Retorna o caminho do avatar do jogador
    pasta = obter_pasta_agente(agente)
    for ext in _EXTENSOES_AVATAR:
        caminho = os.path.join(pasta, f"avatar{ext}")
        if os.path.exists(caminho):
            return caminho
    return None


def salvar_avatar_jogador(agente: str, nome_arquivo: str, conteudo: bytes) -> str:
    # Salva a foto enviada (nome + bytes) como memoria_{agente}/avatar
    if not conteudo:
        return None

    remover_avatar_jogador(agente)

    pasta = obter_pasta_agente(agente)
    extensao = os.path.splitext(os.path.basename(nome_arquivo or ""))[1].lower()
    if extensao not in _EXTENSOES_AVATAR:
        extensao = ".png"
    caminho = os.path.join(pasta, f"avatar{extensao}")

    with open(caminho, "wb") as f:
        f.write(conteudo)

    return caminho


def remover_avatar_jogador(agente: str):
    pasta = obter_pasta_agente(agente)
    for ext in _EXTENSOES_AVATAR:
        caminho = os.path.join(pasta, f"avatar{ext}")
        if os.path.exists(caminho):
            os.remove(caminho)


def carregar_imagem_base64(caminho_imagem: str) -> str:
    # Lê uma imagem local e converte para string Base64.
    with open(caminho_imagem, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def obter_mimetype_imagem(caminho_imagem: str) -> str:
    # Detecta o mimetype correto a partir da extensão do arquivo.
    extensao = os.path.splitext(caminho_imagem)[1].lower()
    mapa_mimetypes = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    return mapa_mimetypes.get(extensao, "image/jpeg")
