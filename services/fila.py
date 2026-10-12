# Fila de requests à LLM: uma ação do mestre vira uma lista de itens (um por personagem) processada
# em segundo plano, um de cada vez. Antes de cada chamada confere os limites RPM/TPM/RPD; se não
# cabe, espera a janela liberar; em erro (ou RPD esgotado) para na vez atual e permite continuar.
# O estado fica em arquivos/fila.json, então sobrevive a reiniciar a API (volta pausada).
import copy
import json
import os
import threading
import time
import uuid

from rpg import limites, previsao
from rpg.memoria import GerenciadorMemoriaRPG
from rpg.paths import ARQUIVOS
from services import eventos, mestre
from services.sessao import LOCK_MESTRE, ErroNegocio, obter as obter_sessao

_CAMINHO = os.path.join(ARQUIVOS, "fila.json")
_G = threading.RLock()
_cancelar = threading.Event()
_agora = time.time  # trocável nos testes
_dormir = time.sleep

_estado: dict | None = None
_carregado = False

ATIVOS = ("rodando", "aguardando_limite")


class _Pausa(Exception):
    pass


class _Cancelada(Exception):
    pass


def _salvar():
    # Chamar com _G.
    os.makedirs(ARQUIVOS, exist_ok=True)
    tmp = _CAMINHO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_estado, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _CAMINHO)
    eventos.publicar("fila_atualizada")


def _carregar():
    global _estado, _carregado
    if _carregado:
        return
    _carregado = True
    try:
        with open(_CAMINHO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception:
        return
    if not isinstance(dados, dict) or dados.get("status") == "concluida":
        return
    if dados.get("status") in ATIVOS:  # a API caiu no meio: nunca retoma sozinha
        dados["status"] = "pausada"
        dados["erro"] = "A API foi reiniciada com a fila em andamento. Clique em Continuar."
        dados["espera_ate"] = None
        for item in dados.get("itens", []):
            if item["status"] in ("verificando", "aguardando", "interpretando"):
                item["status"] = "erro"
                item["erro"] = dados["erro"]
    _estado = dados


def ocupada() -> bool:
    with _G:
        _carregar()
        return bool(_estado) and _estado["status"] in (*ATIVOS, "pausada")


def estado() -> dict | None:
    # Cópia segura para a API (sem caminhos locais nem instruções internas).
    with _G:
        _carregar()
        if not _estado:
            return None
        e = copy.deepcopy(_estado)
    e.pop("imagem_path", None)
    e.pop("presentes", None)
    for item in e["itens"]:
        item.pop("instrucao", None)
    e["limites_ativos"] = limites.controle_ativo()
    e["agora"] = _agora()
    return e


def resetar():
    # Depois de restaurar/reiniciar a mesa.
    global _estado, _carregado
    with _G:
        _carregado = True
        _estado = None
        try:
            os.remove(_CAMINHO)
        except OSError:
            pass
        eventos.publicar("fila_atualizada")


def _apagar_imagem():
    caminho = (_estado or {}).get("imagem_path")
    if caminho and os.path.exists(caminho):
        try:
            os.remove(caminho)
        except OSError:
            pass


def _novo(tipo: str, itens: list[dict], presentes=None, rotulo="", imagem_path=None, alvos=None):
    global _estado
    with _G:
        _carregar()
        if _estado and _estado["status"] in (*ATIVOS, "pausada"):
            raise ErroNegocio("Há uma fila de requests pendente. Continue ou cancele a fila antes de uma nova ação.")
        _cancelar.clear()
        _estado = {
            "id": uuid.uuid4().hex[:8],
            "tipo": tipo,
            "status": "rodando",
            "erro": None,
            "aviso": None,
            "espera_ate": None,
            "indice": 0,
            "presentes": presentes or [],
            "rotulo": rotulo,
            "imagem_path": imagem_path,
            "alvos": alvos or [],
            "mensagens": [],
            "mensagem": None,
            "itens": [
                {"agente": i["agente"], "instrucao": i.get("instrucao", ""), "status": "pendente",
                 "etapa": None, "tokens_previstos": 0, "erro": None}
                for i in itens
            ],
        }
        _salvar()
    _iniciar_thread()


# --- criação (a parte rápida roda na requisição; as chamadas à LLM, na thread) ---

def enfileirar_falar_todos(comando: str, caminho_imagem=None):
    presentes, itens = mestre.preparar_falar_todos(comando)
    _novo("falar_todos", itens, presentes=presentes, imagem_path=caminho_imagem)


def enfileirar_falar_direcionado(alvos: list[str], privado: bool, comando: str, caminho_imagem=None):
    presentes, itens = mestre.preparar_falar_direcionado(alvos, privado, comando)
    _novo("falar_direcionado", itens, presentes=presentes, imagem_path=caminho_imagem)


def enfileirar_chamada(chamada_id: str):
    presentes, itens, rotulo = mestre.preparar_aprovar_chamada(chamada_id)
    _novo("aprovar_chamada", itens, presentes=presentes, rotulo=rotulo)


def enfileirar_finalizar():
    alvos = mestre.preparar_finalizar()
    _novo("finalizar_rodada", [{"agente": a} for a in alvos], alvos=alvos)


def continuar():
    with _G:
        _carregar()
        if not _estado or _estado["status"] != "pausada":
            raise ErroNegocio("Não há fila pausada para continuar.")
        if _estado["indice"] < len(_estado["itens"]):
            item = _estado["itens"][_estado["indice"]]
            item["status"] = "pendente"
            item["erro"] = None
        _estado["status"] = "rodando"
        _estado["erro"] = None
        _cancelar.clear()
        _salvar()
    _iniciar_thread()


def cancelar():
    global _estado
    with _G:
        _carregar()
        if not _estado or _estado["status"] == "concluida":
            return
        if _estado["status"] in ATIVOS:
            _cancelar.set()  # a thread encerra no próximo ponto de checagem
            return
        _apagar_imagem()
        _estado = None
        try:
            os.remove(_CAMINHO)
        except OSError:
            pass
        eventos.publicar("fila_atualizada")


# --- execução ---

def _iniciar_thread():
    threading.Thread(target=_executar, daemon=True, name="fila-requests").start()


def _traduzir_erro(e: Exception) -> str:
    txt = f"{type(e).__name__}: {e}"
    baixo = txt.lower()
    if "429" in baixo or "rate limit" in baixo or "quota" in baixo or "resource_exhausted" in baixo:
        prefixo = "Limite do provedor atingido (429)"
    elif "503" in baixo or "overloaded" in baixo or "unavailable" in baixo or "high demand" in baixo:
        prefixo = "Provedor com alta demanda (503)"
    elif "timeout" in baixo or "timed out" in baixo:
        prefixo = "Tempo esgotado esperando o provedor"
    elif "401" in baixo or "403" in baixo or "api key" in baixo or "unauthorized" in baixo or "permission" in baixo:
        prefixo = "Chave de API inválida ou sem permissão"
    elif "connect" in baixo or "refused" in baixo:
        prefixo = "Não foi possível conectar ao provedor"
    else:
        prefixo = "Erro na chamada à LLM"
    return f"{prefixo} — {txt[:300]}"


def _checar_cancelamento():
    if _cancelar.is_set():
        raise _Cancelada()


def _mutar(item: dict | None = None, **campos):
    # Altera o estado (e o item atual, se informado) e grava.
    with _G:
        for chave in ("status", "erro", "aviso", "espera_ate"):
            if chave in campos:
                _estado[chave] = campos[chave]
        if item is not None:
            for chave in ("etapa", "tokens_previstos"):
                if chave in campos:
                    item[chave] = campos[chave]
            if "item_status" in campos:
                item["status"] = campos["item_status"]
            if "item_erro" in campos:
                item["erro"] = campos["item_erro"]
        _salvar()


def _gate(item: dict, tokens: int, etapa: str | None = None):
    # Antes de cada chamada à LLM: espera a janela de RPM/TPM liberar ou pausa se não adianta esperar.
    _mutar(item, item_status="verificando", tokens_previstos=tokens, etapa=etapa)
    while True:
        _checar_cancelamento()
        bloqueio = limites.espera_necessaria(tokens)
        if bloqueio is None:
            break
        if bloqueio.tipo == "pausa":
            raise _Pausa(bloqueio.mensagem)
        ate = _agora() + bloqueio.segundos
        _mutar(item, status="aguardando_limite", aviso=bloqueio.mensagem, espera_ate=ate, item_status="aguardando")
        while _agora() < ate:
            _checar_cancelamento()
            _dormir(1)
    _mutar(item, status="rodando", aviso=None, espera_ate=None, item_status="interpretando")


def _processar_item(item: dict):
    imagem = _estado["imagem_path"]
    if _estado["tipo"] == "finalizar_rodada":
        GerenciadorMemoriaRPG.finalizar_rodada_agente(
            item["agente"],
            gate=lambda etapa: _gate(item, previsao.prever_etapa(item["agente"], etapa), etapa),
        )
        return
    previsto = previsao.prever_entrada(item["agente"], item["instrucao"], obter_sessao()["historico"], imagem)
    _gate(item, previsto)
    msg = mestre.responder(item["agente"], item["instrucao"], _estado["presentes"], _estado["rotulo"], imagem)
    if msg:
        with _G:
            _estado["mensagens"].append(msg)


def _encerrar(cancelada: bool):
    global _estado
    with _G:
        _apagar_imagem()
        if cancelada:
            _estado = None
            try:
                os.remove(_CAMINHO)
            except OSError:
                pass
            eventos.publicar("fila_atualizada")
        else:
            _estado["status"] = "concluida"
            _salvar()


def _executar():
    with LOCK_MESTRE:
        try:
            while True:
                _checar_cancelamento()
                with _G:
                    i = _estado["indice"]
                    if i >= len(_estado["itens"]):
                        break
                    item = _estado["itens"][i]
                try:
                    _mutar(item, item_status="verificando", item_erro=None)
                    _processar_item(item)
                except (_Cancelada, _Pausa):
                    raise
                except Exception as e:
                    raise _Pausa(_traduzir_erro(e)) from e
                with _G:
                    item["status"] = "ok"
                    _estado["indice"] = i + 1
                    _salvar()

            mensagens = list(_estado["mensagens"])
            if _estado["tipo"] == "finalizar_rodada":
                mensagens.append(mestre.fechar_rodada(_estado["alvos"]))
            with _G:
                _estado["mensagem"] = "\n".join(mensagens) or None
            _encerrar(cancelada=False)
        except _Cancelada:
            _encerrar(cancelada=True)
        except Exception as e:
            motivo = str(e) if isinstance(e, _Pausa) else _traduzir_erro(e)
            with _G:
                i = _estado["indice"]
                item_atual = _estado["itens"][i] if i < len(_estado["itens"]) else None
            _mutar(item_atual, status="pausada", erro=motivo, espera_ate=None, aviso=None,
                   item_status="erro", item_erro=motivo)
