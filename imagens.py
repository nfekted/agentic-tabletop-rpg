# Seleção/entrada de imagens e conversão para uso multimodal (base64 + mimetype).
import os
import base64
import tempfile

from memoria import obter_pasta_agente

_EXTENSOES_AVATAR = (".png", ".jpg", ".jpeg", ".webp")


def selecionar_imagem_interativa(pasta_base: str = "img") -> str:
    # Navegação por pastas via terminal (usada apenas pelo main.py em modo CLI).
    if not os.path.exists(pasta_base):
        print(f"⚠️ A pasta '{pasta_base}' não existe no diretório atual.")
        return None

    pasta_atual = pasta_base

    while True:
        itens = os.listdir(pasta_atual)
        subpastas = [d for d in itens if os.path.isdir(os.path.join(pasta_atual, d))]
        imagens = [
            f
            for f in itens
            if os.path.isfile(os.path.join(pasta_atual, f))
            and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]

        opcoes = []
        print(f"\n📂 Diretório atual: [{pasta_atual}]")

        if pasta_atual != pasta_base:
            opcoes.append(("VOLTAR", ".."))
            print("  0. 🔙 [Voltar pasta]")

        idx = 1
        for sp in subpastas:
            opcoes.append(("PASTA", sp))
            print(f"  {idx}. 📁 {sp}/")
            idx += 1

        for img in imagens:
            opcoes.append(("ARQUIVO", img))
            print(f"  {idx}. 🖼️ {img}")
            idx += 1

        if not subpastas and not imagens:
            print("  (Nenhum arquivo ou subpasta encontrado aqui)")

        escolha = input("\nEscolha o número do item (ou Enter para cancelar): ").strip()

        if not escolha:
            return None

        if not escolha.isdigit():
            print("❌ Por favor, digite um número válido.")
            continue

        num = int(escolha)

        if pasta_atual != pasta_base and num == 0:
            pasta_atual = os.path.dirname(pasta_atual)
            continue

        offset = 1 if pasta_atual != pasta_base else 0

        if 0 <= num - 1 < len(opcoes):
            tipo, nome = opcoes[num - 1]
            caminho_escolhido = os.path.join(pasta_atual, nome)

            if tipo == "PASTA":
                pasta_atual = caminho_escolhido
            elif tipo == "ARQUIVO":
                print(f"✅ Imagem selecionada: {caminho_escolhido}")
                return caminho_escolhido
        else:
            print("❌ Opção fora do limite!")


def salvar_imagem_upload(arquivo_upload) -> str:
    # Salva um arquivo vindo de st.file_uploader em um caminho temporário e retorna o caminho
    if arquivo_upload is None:
        return None

    extensao = os.path.splitext(arquivo_upload.name)[1].lower() or ".jpg"
    pasta_tmp = os.path.join(tempfile.gettempdir(), "rpg_agent_uploads")
    os.makedirs(pasta_tmp, exist_ok=True)
    caminho = os.path.join(pasta_tmp, f"upload_{os.getpid()}_{arquivo_upload.name}")

    with open(caminho, "wb") as f:
        f.write(arquivo_upload.getbuffer())

    return caminho


def caminho_avatar(agente: str) -> str:
    #Retorna o caminho do avatar do jogador
    pasta = obter_pasta_agente(agente)
    for ext in _EXTENSOES_AVATAR:
        caminho = os.path.join(pasta, f"avatar{ext}")
        if os.path.exists(caminho):
            return caminho
    return None


def salvar_avatar_jogador(agente: str, arquivo_upload) -> str:
    #Salva a foto vinda de st.file_uploader como memoria_{agente}/avatar
    if arquivo_upload is None:
        return None

    remover_avatar_jogador(agente)

    pasta = obter_pasta_agente(agente)
    extensao = os.path.splitext(arquivo_upload.name)[1].lower() or ".png"
    if extensao not in _EXTENSOES_AVATAR:
        extensao = ".png"
    caminho = os.path.join(pasta, f"avatar{extensao}")

    with open(caminho, "wb") as f:
        f.write(arquivo_upload.getbuffer())

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
