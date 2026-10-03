# Carregamento/edição de regras e fichas modulares dos personagens.
import json
import math
import os
import re
from rpg.paths import ARQUIVOS

PASTA_BASE = ARQUIVOS
PASTA_REGRAS = os.path.join(PASTA_BASE, "regras")
CAMINHO_REGRA_ATIVA = os.path.join(PASTA_REGRAS, ".ativa")
PASTA_FICHAS = os.path.join(PASTA_BASE, "fichas")


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


# --- FICHA ESTRUTURADA: um .json por seção ({nome}_<seção>.json) ---

# Ordem em que as seções entram no prompt do personagem.
SECOES = ("base", "status", "atributos", "pericias", "habilidades", "itens", "personalidade")

CAMPOS_BASE = (("nome", "Nome"), ("classe", "Classe"), ("passado_origem", "Passado/Origem"))
CAMPOS_PERSONALIDADE = (
    ("tratamento_personalidade", "Tratamento/Personalidade"),
    ("medos_gatilhos", "Medos/Gatilhos"),
    ("segredos_pessoais", "Segredos pessoais"),
)
BLOCOS_HABILIDADES = (("habilidades", "HABILIDADES"), ("poderes", "PODERES"), ("passivas", "PASSIVAS"))
TAMANHO_MOCHILA_PADRAO = 5

CAMINHO_PADRAO = os.path.join(PASTA_BASE, "padrao_ficha.json")


# --- Normalização (ao carregar e ao salvar) ---
# Regra geral: item de lista sem "nome" é descartado; campos opcionais vazios viram "" ou None.

def _texto(valor) -> str:
    return "" if valor is None else str(valor).strip()


def _linha(valor) -> str:
    # Uma linha só (quebras e espaços repetidos viram um espaço): vai assim para o prompt.
    return " ".join(_texto(valor).split())


def _numero(valor, inteiro=False):
    # Número opcional: vazio ou inválido vira None. Aceita vírgula decimal ("1,5").
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        return None
    try:
        n = float(str(valor).replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(n):
        return None
    if inteiro or n == int(n):
        return int(n)
    return round(n, 2)


def _fmt_num(n) -> str:
    return str(int(n)) if n == int(n) else str(round(n, 2))


def _dicts(valor) -> list:
    return [i for i in valor if isinstance(i, dict)] if isinstance(valor, list) else []


def _normalizar_campos(dados, campos) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    return {chave: _texto(dados.get(chave)) for chave, _ in campos}


def _normalizar_base(dados) -> dict:
    return _normalizar_campos(dados, CAMPOS_BASE)


def _normalizar_personalidade(dados) -> dict:
    return _normalizar_campos(dados, CAMPOS_PERSONALIDADE)


def _normalizar_status(lista) -> list:
    saida = []
    for i in _dicts(lista):
        nome = _texto(i.get("nome"))
        if nome:
            saida.append({
                "nome": nome,
                "valor_atual": _numero(i.get("valor_atual"), inteiro=True) or 0,
                "valor_max": _numero(i.get("valor_max"), inteiro=True) or 0,
                "cor": _texto(i.get("cor")) or "#DC143C",
            })
    return saida


def _normalizar_pares(lista) -> list:
    return [
        {"nome": nome, "valor": _texto(i.get("valor"))}
        for i in _dicts(lista)
        if (nome := _texto(i.get("nome")))
    ]


def _normalizar_habilidades(dados) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    return {
        chave: [
            {"nome": nome, "custo": _texto(i.get("custo")), "descricao": _texto(i.get("descricao"))}
            for i in _dicts(dados.get(chave))
            if (nome := _texto(i.get("nome")))
        ]
        for chave, _ in BLOCOS_HABILIDADES
    }


def _normalizar_item(i: dict):
    nome = _texto(i.get("nome"))
    if not nome:
        return None
    return {
        "nome": nome,
        "maos": _numero(i.get("maos"), inteiro=True),
        "peso": _numero(i.get("peso")),
        "alcance": _texto(i.get("alcance")),
        "dano": _texto(i.get("dano")),
        "porcentagem_crit": _numero(i.get("porcentagem_crit"), inteiro=True),
        "multiplicador_critico": _numero(i.get("multiplicador_critico")),
        "descricao": _texto(i.get("descricao")),
    }


def _normalizar_itens(dados) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    tamanho = (
        _numero(dados.get("tamanho_mochila"), inteiro=True)
        if "tamanho_mochila" in dados
        else TAMANHO_MOCHILA_PADRAO
    )
    return {
        "tamanho_mochila": max(0, tamanho or 0),
        "equipamento": [i for i in map(_normalizar_item, _dicts(dados.get("equipamento"))) if i],
        "mochila": [i for i in map(_normalizar_item, _dicts(dados.get("mochila"))) if i],
    }


# --- Padrão de status e atributos: definido uma vez, vale para todos os personagens ---
# {"status": [{"nome", "cor"}], "atributos": [{"nome"}]}; o personagem guarda só os valores.

def _normalizar_padrao(dados) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    status = [
        {"nome": i["nome"], "cor": i["cor"]}
        for i in _normalizar_status(dados.get("status"))
    ]
    atributos = [{"nome": i["nome"]} for i in _normalizar_pares(dados.get("atributos"))]
    return {"status": status, "atributos": atributos}


def padrao_configurado() -> bool:
    return os.path.exists(CAMINHO_PADRAO)


def carregar_padrao() -> dict:
    try:
        with open(CAMINHO_PADRAO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        dados = {}
    return _normalizar_padrao(dados)


def salvar_padrao(dados: dict):
    primeira_vez = not padrao_configurado()
    salvar_arquivo(CAMINHO_PADRAO, json.dumps(_normalizar_padrao(dados), indent=2, ensure_ascii=False))
    if primeira_vez and os.path.isdir(PASTA_FICHAS):
        # Valores de fichas antigas (formato livre) são descartados: todos recomeçam do padrão.
        for arq in os.listdir(PASTA_FICHAS):
            if arq.endswith(("_status.json", "_atributos.json")):
                os.remove(os.path.join(PASTA_FICHAS, arq))


def _aplicar_padrao_status(salvos: list) -> list:
    por_nome = {s["nome"]: s for s in salvos}
    return [
        {
            "nome": p["nome"],
            "cor": p["cor"],
            "valor_atual": por_nome.get(p["nome"], {}).get("valor_atual", 0),
            "valor_max": por_nome.get(p["nome"], {}).get("valor_max", 0),
        }
        for p in carregar_padrao()["status"]
    ]


def _aplicar_padrao_atributos(salvos: list) -> list:
    por_nome = {a["nome"]: a["valor"] for a in salvos}
    return [{"nome": p["nome"], "valor": por_nome.get(p["nome"], "")} for p in carregar_padrao()["atributos"]]


# --- Formatação em markdown para o prompt (seção vazia devolve "" e não entra) ---

def _bloco(titulo: str, linhas: list) -> str:
    return "\n".join([titulo, *linhas]) if linhas else ""


def formatar_base_markdown(base: dict) -> str:
    linhas = [f"- **{rotulo}:** {_linha(base.get(chave))}" for chave, rotulo in CAMPOS_BASE if _linha(base.get(chave))]
    return _bloco("## INFORMAÇÕES BÁSICAS", linhas)


def formatar_status_markdown(status_lista: list) -> str:
    linhas = [f"- **{i['nome']}**: {i['valor_atual']}/{i['valor_max']}" for i in status_lista]
    return _bloco("## STATUS ATUAIS", linhas)


def _formatar_pares(titulo: str, pares: list) -> str:
    linhas = [f"- {p['nome']}: {_linha(p['valor'])}" if _linha(p["valor"]) else f"- {p['nome']}" for p in pares]
    return _bloco(titulo, linhas)


def formatar_atributos_markdown(atributos: list) -> str:
    return _formatar_pares("## ATRIBUTOS", atributos)


def formatar_pericias_markdown(pericias: list) -> str:
    return _formatar_pares("## PERÍCIAS", pericias)


def formatar_habilidades_markdown(habilidades: dict) -> str:
    blocos = []
    for chave, titulo in BLOCOS_HABILIDADES:
        linhas = []
        for h in habilidades.get(chave, []):
            partes = []
            if _linha(h["custo"]):
                partes.append(f"Usa {_linha(h['custo'])}")
            if _linha(h["descricao"]):
                partes.append(_linha(h["descricao"]))
            linhas.append(f"- {h['nome']}: {', '.join(partes)}" if partes else f"- {h['nome']}")
        if linhas:
            blocos.append(_bloco(f"## {titulo}", linhas))
    return "\n\n".join(blocos)


def _linha_item(item: dict, prefixo: str = "") -> str:
    partes = []
    if item["peso"] is not None:
        partes.append(f"peso: {_fmt_num(item['peso'])}")
    if item["maos"] is not None:
        partes.append(f"mãos: {item['maos']}")
    if _linha(item["alcance"]):
        partes.append(_linha(item["alcance"]))
    if _linha(item["dano"]):
        partes.append(f"{_linha(item['dano'])} dano")
    pct, mult = item["porcentagem_crit"], item["multiplicador_critico"]
    if pct is not None and mult is not None:
        partes.append(f"{pct}% crit x{_fmt_num(mult)}")
    elif pct is not None:
        partes.append(f"{pct}% crit")
    elif mult is not None:
        partes.append(f"crit x{_fmt_num(mult)}")
    if _linha(item["descricao"]):
        partes.append(_linha(item["descricao"]))
    nome = f"{prefixo}{item['nome']}"
    return f"- **{nome}:** {', '.join(partes)}" if partes else f"- **{nome}**"


def peso_livre(itens: dict) -> float:
    # Tamanho da mochila menos o peso de tudo que o personagem carrega (equipamento + mochila).
    carregado = sum(i["peso"] or 0 for i in itens["equipamento"] + itens["mochila"])
    return round(itens["tamanho_mochila"] - carregado, 2)


def formatar_itens_markdown(itens: dict) -> str:
    blocos = []
    equipamento = _bloco("## EQUIPAMENTOS", [_linha_item(i) for i in itens["equipamento"]])
    if equipamento:
        blocos.append(equipamento)

    # Na mochila, itens 100% iguais viram uma linha só ("2x Nome") para economizar tokens.
    grupos = {}
    for item in itens["mochila"]:
        grupos.setdefault(json.dumps(item, sort_keys=True), [item, 0])[1] += 1
    linhas = [_linha_item(item, f"{n}x " if n > 1 else "") for item, n in grupos.values()]
    tamanho = itens["tamanho_mochila"]
    if linhas or tamanho > 0:
        corpo = _bloco("## MOCHILA", linhas) or "## MOCHILA"
        if tamanho > 0:
            corpo += ("\n\n" if linhas else "\n") + f"Mochila: {_fmt_num(peso_livre(itens))}/{tamanho} livres"
        blocos.append(corpo)
    return "\n\n".join(blocos)


def formatar_personalidade_markdown(personalidade: dict) -> str:
    linhas = [
        f"- {rotulo}: {_linha(personalidade.get(chave))}"
        for chave, rotulo in CAMPOS_PERSONALIDADE
        if _linha(personalidade.get(chave))
    ]
    return _bloco("## PERSONALIDADE E REGRAS DE INTERPRETAÇÃO (ROLEPLAY)", linhas)


# --- Registro das seções: modelo inicial, normalização e formatação de cada uma ---

_SECOES = {
    "base": (lambda ag: {"nome": ag, "classe": "", "passado_origem": ""}, _normalizar_base, formatar_base_markdown),
    "status": (lambda ag: [], _normalizar_status, formatar_status_markdown),
    "atributos": (lambda ag: [], _normalizar_pares, formatar_atributos_markdown),
    "pericias": (lambda ag: [], _normalizar_pares, formatar_pericias_markdown),
    "habilidades": (lambda ag: {}, _normalizar_habilidades, formatar_habilidades_markdown),
    "itens": (lambda ag: {}, _normalizar_itens, formatar_itens_markdown),
    "personalidade": (lambda ag: {}, _normalizar_personalidade, formatar_personalidade_markdown),
}


# --- Gestão da ficha (carga, gravação, inicialização) ---

def caminhos_subarquivos(agente: str) -> dict:
    nome = agente.strip().lower()
    return {secao: os.path.join(PASTA_FICHAS, f"{nome}_{secao}.json") for secao in SECOES}


def carregar_secao(agente: str, secao: str):
    modelo, normalizar, _ = _SECOES[secao]
    try:
        with open(caminhos_subarquivos(agente)[secao], "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        dados = modelo(agente)
    dados = normalizar(dados)
    if secao == "status":
        return _aplicar_padrao_status(dados)
    if secao == "atributos":
        return _aplicar_padrao_atributos(dados)
    return dados


def salvar_secao(agente: str, secao: str, dados):
    _, normalizar, _ = _SECOES[secao]
    conteudo = json.dumps(normalizar(dados), indent=2, ensure_ascii=False)
    salvar_arquivo(caminhos_subarquivos(agente)[secao], conteudo)


def inicializar_ficha_agente(agente: str):
    # Cria, a partir do modelo, cada arquivo de seção que ainda não existe.
    for secao, caminho in caminhos_subarquivos(agente).items():
        if not os.path.exists(caminho):
            salvar_secao(agente, secao, _SECOES[secao][0](agente))


def carregar_status_jogador(agente: str) -> list:
    inicializar_ficha_agente(agente)
    return carregar_secao(agente, "status")


def salvar_status_jogador(agente: str, lista_status: list):
    salvar_secao(agente, "status", lista_status)


def carregar_subarquivos_ficha(agente: str) -> dict:
    inicializar_ficha_agente(agente)
    return {secao: carregar_secao(agente, secao) for secao in SECOES}


def salvar_subarquivos_ficha(agente: str, dados: dict):
    for secao in SECOES:
        if secao in dados:
            salvar_secao(agente, secao, dados[secao])


def carregar_ficha(agente: str) -> str:
    sub = carregar_subarquivos_ficha(agente)
    blocos = (_SECOES[secao][2](sub[secao]) for secao in SECOES)
    return "\n\n".join(b for b in blocos if b)


def carregar_fichas(agentes) -> dict:
    return {ag: carregar_ficha(ag) for ag in agentes}
