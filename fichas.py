# Carregamento/edição de regras, fichas dos personagens e status (vivo/morto/etc.).
import os
import re

PASTA_REGRAS = "regras"
CAMINHO_REGRA_ATIVA = os.path.join(PASTA_REGRAS, ".ativa")
PASTA_FICHAS = "fichas"


def carregar_arquivo(caminho: str, padrao: str = "") -> str:
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return padrao


def salvar_arquivo(caminho: str, conteudo: str):
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def caminho_regra(nome_arquivo: str) -> str:
    return os.path.join(PASTA_REGRAS, nome_arquivo)


def listar_arquivos_regras() -> list:
    # Lista os arquivos .txt dentro de regras/.
    if not os.path.exists(PASTA_REGRAS):
        os.makedirs(PASTA_REGRAS, exist_ok=True)

    arquivos = sorted(
        f
        for f in os.listdir(PASTA_REGRAS)
        if f.endswith(".txt") and not f.startswith(".")
    )

    return arquivos


def obter_regra_ativa() -> str:
    # Retorna o nome do arquivo (ex: 'combate.txt') atualmente marcado como ativo.
    arquivos = listar_arquivos_regras()
    ativa = carregar_arquivo(CAMINHO_REGRA_ATIVA, "").strip()
    if ativa not in arquivos:
        ativa = arquivos[0]
        definir_regra_ativa(ativa)
    return ativa


def definir_regra_ativa(nome_arquivo: str):
    salvar_arquivo(CAMINHO_REGRA_ATIVA, nome_arquivo)


def carregar_regra(nome_arquivo: str) -> str:
    return carregar_arquivo(caminho_regra(nome_arquivo), "")


def salvar_regra(nome_arquivo: str, conteudo: str):
    salvar_arquivo(caminho_regra(nome_arquivo), conteudo)


def criar_arquivo_regra(nome: str) -> str:
    # Cria um novo conjunto de regras vazio a partir de um nome digitado
    nome = nome.strip()
    if not nome:
        return None

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome).strip("_").lower()
    if not slug:
        return None

    nome_arquivo = f"{slug}.txt"
    if os.path.exists(caminho_regra(nome_arquivo)):
        return None

    salvar_arquivo(caminho_regra(nome_arquivo), "")
    return nome_arquivo


def remover_arquivo_regra(nome_arquivo: str) -> bool:
    # Remove um conjunto de regras. Nunca remove o último restante (sempre precisa haver pelo menos um).
    arquivos = listar_arquivos_regras()
    if nome_arquivo not in arquivos or len(arquivos) <= 1:
        return False

    os.remove(caminho_regra(nome_arquivo))

    if carregar_arquivo(CAMINHO_REGRA_ATIVA, "").strip() == nome_arquivo:
        restantes = [a for a in arquivos if a != nome_arquivo]
        definir_regra_ativa(restantes[0])

    return True


def carregar_regras() -> str:
    # Usada pelo prompt dos agentes: sempre retorna só o conteúdo do conjunto de regras ATIVO no momento
    return carregar_regra(obter_regra_ativa())


def caminho_ficha(agente: str) -> str:
    return os.path.join(PASTA_FICHAS, f"{agente.lower()}.txt")


def carregar_ficha(agente: str) -> str:
    return carregar_arquivo(caminho_ficha(agente), "")


def salvar_ficha(agente: str, conteudo: str):
    salvar_arquivo(caminho_ficha(agente), conteudo)


def carregar_fichas(agentes) -> dict:
    # Monta o dicionário {agente: conteúdo_da_ficha} para a lista de agentes dada.
    return {ag: carregar_ficha(ag) for ag in agentes}


REGRAS = carregar_regras()
FICHAS = {}


def definir_status_jogador(agente: str, status: str):
    # Atualiza (ou insere) a linha 'status: ...' no topo da ficha do agente
    conteudo = carregar_ficha(agente)
    linhas = conteudo.split("\n") if conteudo else []
    if linhas and "status:" in linhas[0].lower():
        linhas[0] = f"status: {status}"
    else:
        linhas.insert(0, f"status: {status}")
    salvar_ficha(agente, "\n".join(linhas))


def obter_status_jogador(agente: str) -> str:
    # Lê a primeira linha da ficha e extrai o status do personagem.
    caminho = caminho_ficha(agente)

    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            primeira_linha = f.readline().strip().lower()
            if "status:" in primeira_linha:
                return primeira_linha.split("status:")[1].strip()

    return "vivo"
