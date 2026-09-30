# Barra "🧠 Contexto" dos cards: quanto do limite da LLM o último prompt do personagem ocupou.
import html

import streamlit as st

from metricas import calcular_contexto

_CORES = {"verde": "#2ecc71", "ambar": "#f39c12", "vermelho": "#e74c3c"}
_NOMES_PARTES = {
    "memoria": "memória",
    "ficha": "ficha",
    "regras": "regras",
    "base": "prompt base",
    "turno": "histórico+instrução",
}


def _fmt(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def _tooltip(ctx: dict) -> str:
    partes = " · ".join(
        f"{_NOMES_PARTES.get(k, k)} {_fmt(v)}" for k, v in ctx["partes"].items()
    )
    linhas = [
        f"Contexto: {ctx['usado']:,} / {ctx['limite']:,} tokens ({ctx['pct']}%)".replace(",", "."),
        f"Gatilho de compressão: {ctx['gatilho_pct']}%",
    ]
    if partes:
        linhas.append(partes)
    if ctx["estimado"]:
        linhas.append("valor estimado (sem medição exata do provedor)")
    if ctx["atualizado_em"]:
        linhas.append(f"medido em {ctx['atualizado_em'].replace('T', ' ')}")
    return html.escape("\n".join(linhas), quote=True).replace("\n", "&#10;")


def html_barra_contexto(nome: str, variante: str = "completo") -> str:
    # Devolve o HTML da barra, ou "" se o controle está desligado / ainda sem medição.
    ctx = calcular_contexto(nome)
    if not ctx:
        return ""
    cor = _CORES[ctx["faixa"]]
    pct = max(0, min(100, ctx["pct"]))
    gatilho = ctx["gatilho_pct"]
    titulo = _tooltip(ctx)
    marcador = (
        f'<span style="position:absolute;left:{gatilho}%;top:0;width:2px;height:100%;'
        f'background:rgba(0,0,0,0.55);"></span>'
    )

    if variante == "inline":
        return (
            f'<span title="{titulo}" style="display:inline-flex;flex-direction:column;'
            f'align-items:center;margin:0 2px;vertical-align:middle;">'
            f'<span style="font-size:9px;font-weight:600;color:{cor};white-space:nowrap;">'
            f"🧠&nbsp;{ctx['pct']:.0f}%</span>"
            f'<span style="display:block;position:relative;width:34px;height:3px;'
            f'background:rgba(128,128,128,0.3);border-radius:2px;overflow:hidden;margin-top:1px;">'
            f'<span style="display:block;width:{pct}%;height:100%;background:{cor};"></span>'
            f"{marcador}</span></span>"
        )

    compacto = variante == "compacto"
    fonte, altura, raio, margem = ("10px", "5px", "3px", "3px") if compacto else ("11px", "8px", "4px", "6px")
    return f"""
    <div title="{titulo}" style="margin-bottom:{margem};">
        <div style="display:flex; justify-content:space-between; font-size:{fonte}; font-weight:600; margin-bottom:2px; color:inherit;">
            <span>🧠 Contexto</span>
            <span style="color:{cor};">{_fmt(ctx['usado'])}/{_fmt(ctx['limite'])}</span>
        </div>
        <div style="position:relative; background:rgba(128,128,128,0.25); border-radius:{raio}; height:{altura}; overflow:hidden; width:100%;">
            <div style="background:{cor}; width:{pct}%; height:100%;"></div>
            {marcador}
        </div>
    </div>
    """


def renderizar_barra_contexto(nome: str, variante: str = "completo"):
    barra = html_barra_contexto(nome, variante)
    if barra:
        st.markdown(barra, unsafe_allow_html=True)
