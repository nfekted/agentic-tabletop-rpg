# Carregamento/edição de regras, fichas dos personagens e status (vivo/morto/etc.).
import os

CAMINHO_REGRAS = "regras_rpg.txt"
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


def carregar_regras() -> str:
    return carregar_arquivo(CAMINHO_REGRAS, "Regras: D20 para testes de habilidade.")


def salvar_regras(conteudo: str):
    salvar_arquivo(CAMINHO_REGRAS, conteudo)


def caminho_ficha(agente: str) -> str:
    return os.path.join(PASTA_FICHAS, f"{agente.lower()}.txt")


def carregar_ficha(agente: str) -> str:
    return carregar_arquivo(caminho_ficha(agente), "")


def salvar_ficha(agente: str, conteudo: str):
    salvar_arquivo(caminho_ficha(agente), conteudo)


def carregar_fichas(agentes) -> dict:
    #Monta o dicionário {agente: conteúdo_da_ficha} para a lista de agentes dada.
    return {ag: carregar_ficha(ag) for ag in agentes}


# Mantido por compatibilidade com o código antigo (main.py / agentes.py usavam
# a constante fixa REGRAS/FICHAS calculada na importação). Agora preferimos
# carregar sob demanda via carregar_regras()/carregar_ficha(), pois o
# Streamlit pode alterar os arquivos em disco a qualquer momento durante a
# mesma sessão do processo.
REGRAS = carregar_regras()
FICHAS = {}


def definir_status_jogador(agente: str, status: str):
    #Atualiza (ou insere) a linha 'status: ...' no topo da ficha do agente, preservando o restante do conteúdo da ficha.
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
