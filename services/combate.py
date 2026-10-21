# Resumo de combate: orquestra a memória dos jogadores e o histórico vivo da sessão.
from rpg import resumo_combate as rc
from rpg.historico import com_audiencia
from rpg import turno as t
from rpg.config import carregar_agentes, carregar_configuracao
from services import desfazer
from services.sessao import obter, salvar


def _participantes() -> list[str]:
    dados = t.carregar_turno() or {}
    agentes = carregar_agentes()
    return [p["nome"] for p in dados.get("personagens", []) if p.get("ordem") is not None and p["nome"] in agentes]


def marcar_inicio() -> bool:
    # Só há memória a marcar com a rodada ativa.
    s = obter()
    if not s["rodada_ativa"]:
        return False
    rc.marcar_inicio(_participantes())
    s["historico"].append(rc.MARCA_COMBATE)
    salvar()
    return True


def trechos() -> dict:
    grupos = rc.trechos_por_grupo(carregar_agentes())
    return {"marcado": bool(grupos), "grupos": grupos}


def deve_sugerir() -> bool:
    limite = int(carregar_configuracao().get("limite_resumo_combate") or 0)
    return limite > 0 and any(g["chars"] >= limite for g in trechos()["grupos"])


def _indice_marca(historico: list[str]) -> int:
    return next((i for i in range(len(historico) - 1, -1, -1) if historico[i] == rc.MARCA_COMBATE), -1)


def aplicar(grupos: list[dict]):
    # grupos: [{agentes, resumo}]. Grupo sem resumo é ignorado. O histórico vivo (prompt de todos e tela do mestre)
    # só é trocado se o maior grupo foi resumido; os demais entram como "(na visão de A, B)".
    validos = [g for g in grupos if g["resumo"].strip()]
    if validos:
        desfazer.invalidar()
    for g in validos:
        rc.aplicar_resumo(g["agentes"], g["resumo"])
    if not validos:
        return

    todos = sorted(grupos, key=lambda g: -len(g["agentes"]))
    principal = todos[0]
    s = obter()
    i = _indice_marca(s["historico"])
    if i >= 0 and principal in validos:
        linhas = [f"{rc.PREFIXO_RESUMO}: {principal['resumo'].strip()}"]
        linhas += [
            com_audiencia(f"{rc.PREFIXO_RESUMO} (na visão de {', '.join(g['agentes'])}): {g['resumo'].strip()}", g["agentes"], carregar_agentes())
            for g in validos if g is not principal
        ]
        s["historico"][i:] = linhas + [rc.MARCA_COMBATE]
        salvar()


def sugerir(agente: str) -> str:
    texto = rc.trecho_normalizado(agente)
    if not texto:
        return ""
    return rc.sugerir_resumo(texto)


def limpar_marca():
    # Fim do combate (ou da rodada): a marca some e o texto fica corrido.
    desfazer.invalidar()
    rc.remover_marca(carregar_agentes())
    s = obter()
    if rc.MARCA_COMBATE in s["historico"]:
        s["historico"][:] = [l for l in s["historico"] if l != rc.MARCA_COMBATE]
        salvar()
