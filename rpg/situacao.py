# Bloco "Situação do combate" do prompt: onde cada participante está e em que estado (calculado na hora).
from rpg.fichas import calcular_situacao, carregar_status_jogador
from rpg.turno import carregar_turno


def _rotulo(nome: str, situacao: str) -> str:
    return f"{nome} ({situacao})" if situacao else nome


def situacao_combate() -> str:
    # Vazio se não há combate em andamento. Nunca pode quebrar a montagem do prompt.
    try:
        dados = carregar_turno()
        if not dados or not dados.get("em_andamento"):
            return ""

        rotulos = {}  # id -> texto do participante
        for p in dados["personagens"]:
            rotulos[p["id"]] = _rotulo(p["nome"], calcular_situacao(carregar_status_jogador(p["nome"])))
        em_combate = {p["id"] for p in dados["personagens"] + dados["tokens"] if p.get("ordem") is not None}
        for k in dados["tokens"]:
            if k["categoria"] == "item":
                rotulos[k["id"]] = f"[Item: {k['nome_exibicao']}]"
            else:
                rotulos[k["id"]] = _rotulo(k["nome_exibicao"], calcular_situacao(k["ficha_dados"].get("status", [])))

        linhas, nas_areas = [], set()
        for a in dados["areas"]:
            ids = [i for i in a["participantes"] if i in rotulos]
            nas_areas.update(ids)
            if ids:
                linhas.append(f"- {a['nome']}: " + ", ".join(rotulos[i] for i in ids))
        soltos = [i for i in rotulos if i not in nas_areas and i in em_combate]
        if soltos:
            linhas.append("- Sem área definida: " + ", ".join(rotulos[i] for i in soltos))
        return "\n".join(linhas)
    except Exception:
        return ""
