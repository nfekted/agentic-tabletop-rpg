# Regras e persistência do Modo por Turnos (arquivos/turno.json)
import json
import os
import re
import uuid
from collections import Counter

from rpg.fichas import salvar_json
from rpg.tokens_manager import carregar_token
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
            dados.setdefault("areas", [])
            dados.setdefault("personagens", [])
            dados.setdefault("tokens", [])
            return dados
    except Exception:
        return None


def salvar_turno(dados: dict) -> None:
    salvar_json(CAMINHO_TURNO, dados)


def _novo_personagem(nome: str) -> dict:
    return {"id": f"p_{nome}", "nome": nome, "ordem": None}


def iniciar_turno(agentes: list[str]) -> dict:
    dados = {
        "em_andamento": False,
        "ordem_atual": None,
        "areas": [],
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


# --- ÁREAS ---

def adicionar_area(nome: str) -> str | None:
    nome = nome.strip()
    if not nome:
        return None
    dados = carregar_turno()
    if not dados:
        return None

    area_id = f"area_{uuid.uuid4().hex[:6]}"
    dados["areas"].append({
        "id": area_id,
        "nome": nome,
        "participantes": [],
    })
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


def vincular_participante(area_id: str, participante_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    for a in dados["areas"]:
        if participante_id in a["participantes"]:
            a["participantes"].remove(participante_id)

    for a in dados["areas"]:
        if a["id"] == area_id:
            if participante_id not in a["participantes"]:
                a["participantes"].append(participante_id)
            salvar_turno(dados)
            return True
    return False


def desvincular_participante(participante_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    alterado = False
    for a in dados["areas"]:
        if participante_id in a["participantes"]:
            a["participantes"].remove(participante_id)
            alterado = True

    if alterado:
        salvar_turno(dados)
    return alterado


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
            p["ordem"] for p in (dados["personagens"] + dados["tokens"])
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
        "ficha_dados": {
            "conteudo": conteudo,
            "status": [],
        },
    }
    dados["tokens"].append(novo_token)
    salvar_turno(dados)
    return novo_token


def remover_token_do_turno(token_id: str) -> bool:
    dados = carregar_turno()
    if not dados:
        return False

    desvincular_participante(token_id)
    dados = carregar_turno()
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
                s["valor_atual"] = max(0, min(maximo, int(s.get("valor_atual") or 0) + delta))
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


def avancar_proxima_acao(turno_dados: dict) -> tuple[bool, str]:
    empates = verificar_empates(turno_dados)
    if empates:
        return False, f"⚠️ Empate detectado na(s) ordem(ns): {', '.join(map(str, empates))}. Defina ordens distintas!"

    fila = obter_fila_ordens(turno_dados)
    if not fila:
        return False, "⚠️ Nenhum participante possui uma ordem definida (mínimo 1)."

    def passar_para(ordem: int, prefixo: str) -> tuple[bool, str]:
        turno_dados["ordem_atual"] = ordem
        salvar_turno(turno_dados)
        participante = obter_participante_por_ordem(turno_dados, ordem)
        nome = participante.get("nome") or participante.get("nome_exibicao", "Participante")
        return True, f"{prefixo}Turno de **{nome}** (Ordem #{ordem})."

    if not turno_dados.get("em_andamento"):
        turno_dados["em_andamento"] = True
        return passar_para(fila[0], "⚔️ Combate iniciado! ")

    ordem_atual = turno_dados.get("ordem_atual")
    if ordem_atual is None or ordem_atual not in fila or ordem_atual >= fila[-1]:
        return passar_para(fila[0], "🔄 Nova Rodada iniciada! ")
    return passar_para(fila[fila.index(ordem_atual) + 1], "")
