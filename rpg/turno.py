# Regras e persistência do Modo por Turnos (arquivos/turno.json)
import json
import os
import re
import uuid
from collections import Counter

from rpg.fichas import salvar_json
from rpg.tokens_manager import carregar_ficha_token, carregar_token
from rpg.paths import ARQUIVOS

CAMINHO_TURNO = os.path.join(ARQUIVOS, "turno.json")

ICONES_CATEGORIA = {
    "inimigo": "⚔️",
    "npc": "👤",
    "item": "🎒",
}


def turno_ativo() -> bool:
    return os.path.exists(CAMINHO_TURNO)


def carregar_turno() -> dict | None:
    if not turno_ativo():
        return None
    try:
        with open(CAMINHO_TURNO, "r", encoding="utf-8") as f:
            dados = json.load(f)
            dados.setdefault("em_andamento", False)
            dados.setdefault("ordem_atual", None)
            dados.setdefault("mapa", None)
            dados.setdefault("areas", [])
            dados.setdefault("obstaculos", [])
            dados.setdefault("personagens", [])
            dados.setdefault("tokens", [])
            for p in dados["personagens"] + dados["tokens"]:
                p.setdefault("tamanho", {"largura": 1, "altura": 1})
            return dados
    except Exception:
        return None


def salvar_turno(dados: dict) -> None:
    salvar_json(CAMINHO_TURNO, dados)


def _novo_personagem(nome: str) -> dict:
    return {"id": f"p_{nome}", "nome": nome, "ordem": None, "pos": None, "tamanho": {"largura": 1, "altura": 1}}


def iniciar_turno(agentes: list[str]) -> dict:
    dados = {
        "em_andamento": False,
        "ordem_atual": None,
        "mapa": None,
        "areas": [],
        "obstaculos": [],
        "personagens": [_novo_personagem(ag) for ag in agentes],
        "tokens": [],
    }
    salvar_turno(dados)
    return dados


def encerrar_turno() -> bool:
    if turno_ativo():
        try:
            os.remove(CAMINHO_TURNO)
            return True
        except Exception:
            return False
    return False


def sincronizar_personagens(agentes: list[str]) -> dict:
    dados = carregar_turno()
    if not dados:
        return iniciar_turno(agentes)

    nomes_existentes = {p["nome"] for p in dados["personagens"]}
    alterado = False
    for ag in agentes:
        if ag not in nomes_existentes:
            dados["personagens"].append(_novo_personagem(ag))
            alterado = True

    if alterado:
        salvar_turno(dados)
    return dados


# --- MAPA E ÁREAS ---
# Mapa em grade (x, y a partir de 0). Áreas são retângulos sem sobreposição; cada participante
# ocupa um retângulo (pos = canto superior esquerdo + tamanho) ou fica fora do mapa (pos = None).
# As áreas de alguém são deduzidas desse retângulo (pode estar em mais de uma).
# Obstáculos (armário, mesa...) são retângulos que bloqueiam células; podem ficar dentro de áreas,
# mas não sobrepõem outro obstáculo. Nada disso vai para o prompt além do nome da área.

MAPA_MAX = 100


def _participante(dados: dict, participante_id: str) -> dict | None:
    for p in dados["personagens"] + dados["tokens"]:
        if p["id"] == participante_id:
            return p
    return None


def _ret(p: dict, pos: dict | None = None, tamanho: dict | None = None) -> dict | None:
    # Retângulo que o participante ocupa (ou ocuparia com outra posição/tamanho); None fora do mapa.
    pos = pos or p.get("pos")
    if not pos:
        return None
    return {"x": pos["x"], "y": pos["y"], **(tamanho or p["tamanho"])}


def _sobreposto(ret: dict, outros: list[dict]) -> dict | None:
    return next(
        (o for o in outros
         if ret["x"] < o["x"] + o["largura"] and o["x"] < ret["x"] + ret["largura"]
         and ret["y"] < o["y"] + o["altura"] and o["y"] < ret["y"] + ret["altura"]),
        None,
    )


def _cabe(mapa: dict, ret: dict) -> bool:
    return (ret["largura"] >= 1 and ret["altura"] >= 1 and ret["x"] >= 0 and ret["y"] >= 0
            and ret["x"] + ret["largura"] <= mapa["largura"] and ret["y"] + ret["altura"] <= mapa["altura"])


def areas_do_participante(dados: dict, p: dict) -> list[dict]:
    ret = _ret(p)
    if not ret:
        return []
    return [a for a in dados["areas"] if _sobreposto(ret, [a])]


def _validar_lugar(dados: dict, p: dict, ret: dict) -> None:
    if not _cabe(dados["mapa"], ret):
        raise ValueError("Não cabe no mapa nessa posição.")
    outros = [r for o in dados["personagens"] + dados["tokens"] if o is not p and (r := _ret(o))]
    if _sobreposto(ret, outros):
        raise ValueError("Célula ocupada.")
    if _sobreposto(ret, dados["obstaculos"]):
        raise ValueError("Célula bloqueada por um obstáculo.")


def criar_mapa(largura: int, altura: int) -> bool:
    dados = carregar_turno()
    if not dados:
        return False
    if dados["mapa"]:
        raise ValueError("Já existe um mapa. Exclua-o para criar outro.")
    if not (1 <= largura <= MAPA_MAX and 1 <= altura <= MAPA_MAX):
        raise ValueError(f"Largura e altura devem estar entre 1 e {MAPA_MAX}.")
    dados["mapa"] = {"largura": largura, "altura": altura}
    salvar_turno(dados)
    return True


def excluir_mapa() -> bool:
    # Leva junto as áreas, os obstáculos e as posições.
    dados = carregar_turno()
    if not dados or not dados["mapa"]:
        return False
    dados["mapa"] = None
    dados["areas"] = []
    dados["obstaculos"] = []
    for p in dados["personagens"] + dados["tokens"]:
        p["pos"] = None
    salvar_turno(dados)
    return True


def adicionar_area(nome: str, x: int, y: int, largura: int, altura: int) -> str | None:
    nome = nome.strip()
    dados = carregar_turno()
    if not dados:
        return None
    mapa = dados["mapa"]
    if not mapa:
        raise ValueError("Crie o mapa antes das áreas.")
    if not nome:
        raise ValueError("Nome da área inválido.")
    ret = {"x": x, "y": y, "largura": largura, "altura": altura}
    if not _cabe(mapa, ret):
        raise ValueError("A área precisa caber dentro do mapa.")
    outra = _sobreposto(ret, dados["areas"])
    if outra:
        raise ValueError(f"A área sobrepõe \"{outra['nome']}\".")

    area_id = f"area_{uuid.uuid4().hex[:6]}"
    dados["areas"].append({"id": area_id, "nome": nome, **ret})
    salvar_turno(dados)
    return area_id


def remover_area(area_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    areas_antes = len(dados["areas"])
    dados["areas"] = [a for a in dados["areas"] if a["id"] != area_id]
    if len(dados["areas"]) < areas_antes:
        salvar_turno(dados)
        return True
    return False


def posicionar_participante(participante_id: str, x: int, y: int) -> bool:
    dados = carregar_turno()
    if not dados:
        return False
    p = _participante(dados, participante_id)
    if not p:
        return False
    mapa = dados["mapa"]
    if not mapa:
        raise ValueError("Não há mapa.")
    pos = {"x": x, "y": y}
    _validar_lugar(dados, p, _ret(p, pos=pos))
    p["pos"] = pos
    salvar_turno(dados)
    return True


def redimensionar_participante(participante_id: str, largura: int, altura: int) -> bool:
    # No mapa, o novo tamanho precisa caber a partir da posição atual.
    dados = carregar_turno()
    if not dados:
        return False
    p = _participante(dados, participante_id)
    if not p:
        return False
    if not (1 <= largura <= MAPA_MAX and 1 <= altura <= MAPA_MAX):
        raise ValueError(f"Largura e altura devem estar entre 1 e {MAPA_MAX}.")
    tamanho = {"largura": largura, "altura": altura}
    if p.get("pos"):
        _validar_lugar(dados, p, _ret(p, tamanho=tamanho))
    p["tamanho"] = tamanho
    salvar_turno(dados)
    return True


def retirar_do_mapa(participante_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False
    p = _participante(dados, participante_id)
    if not p:
        return False
    if p.get("pos"):
        p["pos"] = None
        salvar_turno(dados)
    return True


def adicionar_obstaculo(nome: str, x: int, y: int, largura: int, altura: int) -> str | None:
    dados = carregar_turno()
    if not dados:
        return None
    mapa = dados["mapa"]
    if not mapa:
        raise ValueError("Crie o mapa antes dos obstáculos.")
    ret = {"x": x, "y": y, "largura": largura, "altura": altura}
    if not _cabe(mapa, ret):
        raise ValueError("O obstáculo precisa caber dentro do mapa.")
    if _sobreposto(ret, dados["obstaculos"]):
        raise ValueError("O obstáculo sobrepõe outro obstáculo.")
    for p in dados["personagens"] + dados["tokens"]:
        if _sobreposto(ret, [r for r in [_ret(p)] if r]):
            raise ValueError("Há participantes nessas células. Mova-os antes de criar o obstáculo.")

    obstaculo_id = f"obs_{uuid.uuid4().hex[:6]}"
    dados["obstaculos"].append({"id": obstaculo_id, "nome": nome.strip(), **ret})
    salvar_turno(dados)
    return obstaculo_id


def remover_obstaculo(obstaculo_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    antes = len(dados["obstaculos"])
    dados["obstaculos"] = [o for o in dados["obstaculos"] if o["id"] != obstaculo_id]
    if len(dados["obstaculos"]) < antes:
        salvar_turno(dados)
        return True
    return False


# --- TOKENS NO TURNO ---


def _gerar_nome_exibicao_token(nome_base: str, tokens_existentes: list[dict]) -> str:
    nome_limpo = re.sub(r"\.txt$", "", nome_base, flags=re.IGNORECASE)
    nome_limpo = nome_limpo.replace("_", " ").title().strip()

    padrao = re.compile(rf"^{re.escape(nome_limpo)}(?:\s+(\d+))?$", re.IGNORECASE)
    numeros_usados = []
    sem_numero_encontrado = False

    for t in tokens_existentes:
        exibicao = t.get("nome_exibicao", "")
        match = padrao.match(exibicao)
        if match:
            num_str = match.group(1)
            if num_str:
                numeros_usados.append(int(num_str))
            else:
                sem_numero_encontrado = True

    if not numeros_usados and not sem_numero_encontrado:
        return f"{nome_limpo} 1"

    proximo = max(numeros_usados or [1 if sem_numero_encontrado else 0]) + 1
    return f"{nome_limpo} {proximo}"


def adicionar_token_ao_turno(categoria: str, nome_arquivo: str) -> dict | None:
    dados = carregar_turno()
    if not dados:
        return None

    conteudo = carregar_token(categoria, nome_arquivo)
    nome_exibicao = _gerar_nome_exibicao_token(nome_arquivo, dados["tokens"])
    token_id = f"tok_{uuid.uuid4().hex[:6]}"
    icone = ICONES_CATEGORIA.get(categoria.lower(), "👾")

    # em combate, o token entra no fim da fila
    ordem_inicial = None
    if dados["em_andamento"]:
        ordens_existentes = [
            p["ordem"]
            for p in (dados["personagens"] + dados["tokens"])
            if p.get("ordem") is not None
        ]
        ordem_inicial = (max(ordens_existentes) + 1) if ordens_existentes else 1

    novo_token = {
        "id": token_id,
        "nome_exibicao": nome_exibicao,
        "categoria": categoria,
        "arquivo": nome_arquivo,
        "tipo_icone": icone,
        "ordem": ordem_inicial,
        "pos": None,
        "tamanho": {"largura": 1, "altura": 1},
        "ficha_dados": {
            "conteudo": conteudo,
            **carregar_ficha_token(categoria, nome_arquivo),
        },
    }
    dados["tokens"].append(novo_token)
    salvar_turno(dados)
    return novo_token


def remover_token_do_turno(token_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    antes = len(dados["tokens"])
    dados["tokens"] = [t for t in dados["tokens"] if t["id"] != token_id]
    if len(dados["tokens"]) < antes:
        salvar_turno(dados)
        return True
    return False


def atualizar_ficha_token(token_id: str, nova_ficha_dados: dict) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    for t in dados["tokens"]:
        if t["id"] == token_id:
            t["ficha_dados"] = nova_ficha_dados
            salvar_turno(dados)
            return True
    return False


def ajustar_status_token(token_id: str, nome_status: str, delta: int) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    for t in dados["tokens"]:
        if t["id"] != token_id:
            continue
        for s in t["ficha_dados"].get("status", []):
            if s.get("nome") == nome_status:
                maximo = int(s.get("valor_max") or 0)
                s["valor_atual"] = max(
                    0, min(maximo, int(s.get("valor_atual") or 0) + delta)
                )
                salvar_turno(dados)
                return True
    return False


# --- GESTÃO DE ORDENS E FLUXO ---


def atualizar_ordem_participante(participante_id: str, ordem: int | None) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    for p in dados["personagens"] + dados["tokens"]:
        if p["id"] == participante_id:
            p["ordem"] = int(ordem) if ordem is not None and ordem > 0 else None
            salvar_turno(dados)
            return True
    return False


def verificar_empates(turno_dados: dict) -> list[int]:
    ordens = Counter(
        p["ordem"]
        for p in turno_dados.get("personagens", []) + turno_dados.get("tokens", [])
        if p.get("ordem") is not None and p["ordem"] > 0
    )
    return sorted(o for o, n in ordens.items() if n > 1)


def obter_fila_ordens(turno_dados: dict) -> list[int]:
    ordens = set()
    for p in turno_dados.get("personagens", []) + turno_dados.get("tokens", []):
        ordem = p.get("ordem")
        if ordem is not None and ordem > 0:
            ordens.add(ordem)
    return sorted(ordens)


def obter_participante_por_ordem(turno_dados: dict, ordem: int | None) -> dict | None:
    if ordem is None:
        return None
    for p in turno_dados.get("personagens", []) + turno_dados.get("tokens", []):
        if p.get("ordem") == ordem:
            return p
    return None


def avancar_proxima_acao(turno_dados: dict) -> tuple[bool, str, str | None]:
    # Devolve (ok, mensagem, evento): evento é "inicio" (combate começou) ou "nova_rodada" (a ordem voltou ao primeiro).
    empates = verificar_empates(turno_dados)
    if empates:
        return (
            False,
            f"⚠️ Empate detectado na(s) ordem(ns): {', '.join(map(str, empates))}. Defina ordens distintas!",
            None,
        )

    fila = obter_fila_ordens(turno_dados)
    if not fila:
        return (
            False,
            "⚠️ Nenhum participante possui uma ordem definida (mínimo 1).",
            None,
        )

    def passar_para(
        ordem: int, prefixo: str, evento: str | None
    ) -> tuple[bool, str, str | None]:
        turno_dados["ordem_atual"] = ordem
        salvar_turno(turno_dados)
        participante = obter_participante_por_ordem(turno_dados, ordem)
        nome = participante.get("nome") or participante.get(
            "nome_exibicao", "Participante"
        )
        return True, f"{prefixo}Turno de **{nome}** (Ordem #{ordem}).", evento

    if not turno_dados.get("em_andamento"):
        turno_dados["em_andamento"] = True
        return passar_para(fila[0], "⚔️ Combate iniciado! ", "inicio")

    ordem_atual = turno_dados.get("ordem_atual")
    if ordem_atual is None or ordem_atual not in fila or ordem_atual >= fila[-1]:
        return passar_para(fila[0], "🔄 Nova Rodada iniciada! ", "nova_rodada")
    return passar_para(fila[fila.index(ordem_atual) + 1], "", None)
