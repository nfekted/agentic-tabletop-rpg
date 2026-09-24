# Carregamento/edição de regras e fichas modulares dos personagens.
import json
import os
import re

PASTA_BASE = "arquivos"
PASTA_REGRAS = os.path.join(PASTA_BASE, "regras")
CAMINHO_REGRA_ATIVA = os.path.join(PASTA_REGRAS, ".ativa")
PASTA_FICHAS = os.path.join(PASTA_BASE, "fichas")

TEMPLATE_BASE = """## INFORMAÇÕES BÁSICAS
- **Nome:** [Nome do Personagem]
- **Classe/Ocupação:** [Classe]
- **Passado/Origem:** [Passado]"""

TEMPLATE_STATUS = [
    {
        "nome": "Vida Atual",
        "valor_atual": 1,
        "valor_max": 10,
        "cor": "#DC143C",
    },
    {
        "nome": "Mana Atual",
        "valor_atual": 1,
        "valor_max": 10,
        "cor": "#6495ED",
    },
]

TEMPLATE_GERAL = """## ATRIBUTOS E PERÍCIAS
- **Atributos:** Força: 10, Agilidade: 12, Intelecto: 14
- **Perícias:** Atletismo, Percepção, Vontade."""

TEMPLATE_HABILIDADES = """## HABILIDADES
- **Habilidade 1**: Gaste X recursos para realizar ação.

## PODERES
- **Poder 1**: Gaste Y recursos para realizar ação.

## PASSIVAS
- **Passiva 1**: Efeito passivo constante."""

TEMPLATE_ITENS = """## EQUIPAMENTOS
- **[Nome do Equipamento]**: Descrição e atributos do equipamento.

## MOCHILA
- **1x [Nome do Item]**: Descrição do item e efeitos."""

TEMPLATE_PERSONALIDADE = """## PERSONALIDADE E REGRAS DE INTERPRETAÇÃO (ROLEPLAY)
- **Tratamento:** Forma como o personagem interage socialmente.
- **Medos e Gatilhos:** Fobias e traumas.
- **Segredos Pessoais:** Informações confidenciais de background."""


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
    if not os.path.exists(PASTA_REGRAS):
        os.makedirs(PASTA_REGRAS, exist_ok=True)

    arquivos = sorted(
        f
        for f in os.listdir(PASTA_REGRAS)
        if f.endswith(".txt") and not f.startswith(".")
    )

    return arquivos


def obter_regra_ativa() -> str:
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
    arquivos = listar_arquivos_regras()
    if nome_arquivo not in arquivos or len(arquivos) <= 1:
        return False

    os.remove(caminho_regra(nome_arquivo))

    if carregar_arquivo(CAMINHO_REGRA_ATIVA, "").strip() == nome_arquivo:
        restantes = [a for a in arquivos if a != nome_arquivo]
        definir_regra_ativa(restantes[0])

    return True


def carregar_regras() -> str:
    return carregar_regra(obter_regra_ativa())


# --- GESTÃO MODULAR DE FICHAS ---

def caminhos_subarquivos(agente: str) -> dict:
    nome = agente.strip().lower()
    return {
        "base": os.path.join(PASTA_FICHAS, f"{nome}_base.txt"),
        "status": os.path.join(PASTA_FICHAS, f"{nome}_status.json"),
        "geral": os.path.join(PASTA_FICHAS, f"{nome}_geral.txt"),
        "habilidades": os.path.join(PASTA_FICHAS, f"{nome}_habilidades.txt"),
        "itens": os.path.join(PASTA_FICHAS, f"{nome}_itens.txt"),
        "personalidade": os.path.join(PASTA_FICHAS, f"{nome}_personalidade.txt"),
    }


def formatar_status_markdown(status_lista: list) -> str:
    linhas = ["## STATUS ATUAIS"]
    if not status_lista:
        linhas.append("- Nenhum status configurado.")
    for item in status_lista:
        nome = item.get("nome", "Status")
        atual = item.get("valor_atual", 0)
        maximo = item.get("valor_max", 0)
        linhas.append(f"- **{nome}**: {atual}/{maximo}")
    return "\n".join(linhas)


def carregar_status_jogador(agente: str) -> list:
    caminhos = caminhos_subarquivos(agente)
    if not os.path.exists(caminhos["status"]):
        inicializar_ficha_agente(agente)
    try:
        with open(caminhos["status"], "r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                return dados
    except Exception:
        pass
    return TEMPLATE_STATUS


def salvar_status_jogador(agente: str, lista_status: list):
    caminhos = caminhos_subarquivos(agente)
    salvar_arquivo(caminhos["status"], json.dumps(lista_status, indent=2, ensure_ascii=False))


def migrar_ficha_legada(agente: str) -> bool:
    """Migra uma ficha monolítica antiga (<nome>.txt) para os 6 subarquivos modulares."""
    nome = agente.strip().lower()
    caminho_legado = os.path.join(PASTA_FICHAS, f"{nome}.txt")
    if not os.path.exists(caminho_legado):
        return False

    conteudo = carregar_arquivo(caminho_legado, "")
    if not conteudo:
        return False

    # Divide o arquivo em seções separadas por cabeçalhos markdown nível 2 (## )
    secoes = re.split(r"(?m)^##\s+", conteudo)
    mapa_secoes = {}
    for bloco in secoes[1:]:
        linhas = bloco.split("\n", 1)
        titulo = linhas[0].strip().upper()
        corpo = linhas[1].strip() if len(linhas) > 1 else ""
        mapa_secoes[titulo] = f"## {linhas[0].strip()}\n{corpo}".strip()

    # 1. Base
    bloco_base = ""
    for k in mapa_secoes:
        if "INFORMA" in k:
            bloco_base = mapa_secoes[k]
            break
    if not bloco_base:
        bloco_base = TEMPLATE_BASE.replace("[Nome do Personagem]", agente)

    # 2. Status
    status_lista = []
    bloco_status_txt = ""
    for k in mapa_secoes:
        if "STATUS" in k:
            bloco_status_txt = mapa_secoes[k]
            break

    if bloco_status_txt:
        # Tenta extrair linhas como - **PV:** 22/22 ou - **Vida:** 10/10
        padrao_status = re.findall(
            r"-\s*\*\*([^:*]+)[:*]+\s*(\d+)\s*/\s*(\d+)", bloco_status_txt
        )
        cores_conhecidas = {
            "pv": "#DC143C",
            "vida": "#DC143C",
            "pe": "#6495ED",
            "mana": "#6495ED",
            "mp": "#6495ED",
            "san": "#9370DB",
            "sanidade": "#9370DB",
            "def": "#2E8B57",
        }
        for st_nome, v_at, v_mx in padrao_status:
            chave_cor = st_nome.strip().lower()
            cor = cores_conhecidas.get(chave_cor, "#4CAF50")
            status_lista.append({
                "nome": st_nome.strip(),
                "valor_atual": int(v_at),
                "valor_max": int(v_mx),
                "cor": cor,
            })

    if not status_lista:
        status_lista = [
            {"nome": "Vida Atual", "valor_atual": 10, "valor_max": 10, "cor": "#DC143C"},
            {"nome": "Mana Atual", "valor_atual": 10, "valor_max": 10, "cor": "#6495ED"},
        ]

    # 3. Geral (Atributos e Perícias)
    blocos_geral = []
    for k in mapa_secoes:
        if "ATRIBUTO" in k or "PERICIA" in k or "PERÍCIA" in k:
            blocos_geral.append(mapa_secoes[k])
    bloco_geral = "\n\n".join(blocos_geral) if blocos_geral else TEMPLATE_GERAL

    # 4. Habilidades (Habilidades, Poderes, Passivas)
    blocos_hab = []
    for k in mapa_secoes:
        if "HABILIDADE" in k or "PODER" in k or "PASSIVA" in k:
            blocos_hab.append(mapa_secoes[k])
    bloco_hab = "\n\n".join(blocos_hab) if blocos_hab else TEMPLATE_HABILIDADES

    # 5. Itens (Equipamentos, Mochila, Itens)
    blocos_itens = []
    for k in mapa_secoes:
        if "EQUIPAMENTO" in k or "MOCHILA" in k or "ITEM" in k or "ITENS" in k:
            blocos_itens.append(mapa_secoes[k])
    bloco_itens = "\n\n".join(blocos_itens) if blocos_itens else TEMPLATE_ITENS

    # 6. Personalidade
    bloco_pers = ""
    for k in mapa_secoes:
        if "PERSONALIDADE" in k or "ROLEPLAY" in k:
            bloco_pers = mapa_secoes[k]
            break
    if not bloco_pers:
        bloco_pers = TEMPLATE_PERSONALIDADE

    # Salva os 6 subarquivos
    caminhos = caminhos_subarquivos(agente)
    salvar_arquivo(caminhos["base"], bloco_base)
    salvar_status_jogador(agente, status_lista)
    salvar_arquivo(caminhos["geral"], bloco_geral)
    salvar_arquivo(caminhos["habilidades"], bloco_hab)
    salvar_arquivo(caminhos["itens"], bloco_itens)
    salvar_arquivo(caminhos["personalidade"], bloco_pers)

    return True


def inicializar_ficha_agente(agente: str):
    """Garante que os 6 subarquivos do agente existam. Se houver legado, migra; senão, cria com templates."""
    caminhos = caminhos_subarquivos(agente)
    if os.path.exists(caminhos["base"]) and os.path.exists(caminhos["status"]):
        return

    # Tenta migrar de arquivo legado se existir
    if migrar_ficha_legada(agente):
        return

    # Senão, cria a partir dos templates padrão
    salvar_arquivo(
        caminhos["base"],
        TEMPLATE_BASE.replace("[Nome do Personagem]", agente),
    )
    salvar_status_jogador(agente, TEMPLATE_STATUS)
    salvar_arquivo(caminhos["geral"], TEMPLATE_GERAL)
    salvar_arquivo(caminhos["habilidades"], TEMPLATE_HABILIDADES)
    salvar_arquivo(caminhos["itens"], TEMPLATE_ITENS)
    salvar_arquivo(caminhos["personalidade"], TEMPLATE_PERSONALIDADE)


def carregar_subarquivos_ficha(agente: str) -> dict:
    inicializar_ficha_agente(agente)
    caminhos = caminhos_subarquivos(agente)
    return {
        "base": carregar_arquivo(caminhos["base"], TEMPLATE_BASE),
        "status": carregar_status_jogador(agente),
        "geral": carregar_arquivo(caminhos["geral"], TEMPLATE_GERAL),
        "habilidades": carregar_arquivo(caminhos["habilidades"], TEMPLATE_HABILIDADES),
        "itens": carregar_arquivo(caminhos["itens"], TEMPLATE_ITENS),
        "personalidade": carregar_arquivo(caminhos["personalidade"], TEMPLATE_PERSONALIDADE),
    }


def salvar_subarquivos_ficha(agente: str, dados: dict):
    caminhos = caminhos_subarquivos(agente)
    if "base" in dados:
        salvar_arquivo(caminhos["base"], dados["base"])
    if "status" in dados:
        salvar_status_jogador(agente, dados["status"])
    if "geral" in dados:
        salvar_arquivo(caminhos["geral"], dados["geral"])
    if "habilidades" in dados:
        salvar_arquivo(caminhos["habilidades"], dados["habilidades"])
    if "itens" in dados:
        salvar_arquivo(caminhos["itens"], dados["itens"])
    if "personalidade" in dados:
        salvar_arquivo(caminhos["personalidade"], dados["personalidade"])


def carregar_ficha(agente: str) -> str:
    """Compila os 6 subarquivos do agente rigorosamente na ordem especificada:
    1. <nome>_base.txt
    2. Formatação textual de <nome>_status.json
    3. <nome>_geral.txt
    4. <nome>_habilidades.txt
    5. <nome>_itens.txt
    6. <nome>_personalidade.txt
    """
    sub = carregar_subarquivos_ficha(agente)
    status_formatado = formatar_status_markdown(sub["status"])

    blocos = [
        sub["base"].strip(),
        status_formatado.strip(),
        sub["geral"].strip(),
        sub["habilidades"].strip(),
        sub["itens"].strip(),
        sub["personalidade"].strip(),
    ]
    return "\n\n".join(b for b in blocos if b)


def carregar_fichas(agentes) -> dict:
    return {ag: carregar_ficha(ag) for ag in agentes}
