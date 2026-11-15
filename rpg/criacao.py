# Criação de personagem pela IA: a partir de uma descrição do mestre, devolve uma ficha estruturada para revisão.
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from rpg.config import carregar_agentes, obter_llm
from rpg.fichas import (
    carregar_padrao,
    carregar_regras,
    carregar_secao,
    normalizar_ficha,
)
from rpg.limites import invocar
from rpg.memoria import texto_resposta

_INSTRUCOES = """# CRIAÇÃO DE PERSONAGEM
Você cria personagens jogáveis para uma mesa de RPG cooperativo. O mestre descreve o personagem que quer e você monta a ficha completa.

## COMO CRIAR
- Siga a descrição do mestre: o que ele pediu é obrigatório; o que ele não disse, você completa com coerência.
- Siga as REGRAS DO SISTEMA abaixo para valores de atributos, status, perícias, custos e itens iniciais (pontos, limites, dados). Se as regras não disserem, use valores modestos de personagem iniciante.
- Use EXATAMENTE os nomes de status e de atributos da mesa listados abaixo, todos eles e nenhum outro. Comece cada status cheio (valor_atual igual a valor_max), salvo quando as regras ou a origem disserem outra coisa.
- Complemente o grupo: veja os PERSONAGENS JÁ NA MESA e evite repetir a mesma função, nome ou história, a menos que o mestre peça.
- Personalidade, medos e segredos devem dar ganchos de roleplay; itens e habilidades devem ser coerentes com a classe e a história.
- Antes de responder, confira todas as contas exigidas pelas regras e pelo mestre (pontos de atributo, quantidade de perícias, valores de status): use todos os pontos disponíveis, sem faltar nem sobrar.

## RESPOSTA
Responda SOMENTE com um objeto JSON no formato abaixo, sem nenhum texto antes ou depois. Campos sem valor ficam "" (texto), null (número) ou [] (lista)."""

_ESQUEMA = """{
  "base": {"nome": "Nome completo", "classe": "", "passado_origem": "uma frase sobre quem é e sua motivação", "detalhes_adicionais": "idade, aparência e outras características"},
  "status": [{"nome": "nome do status da mesa", "valor_atual": 0, "valor_max": 0}],
  "atributos": [{"nome": "nome do atributo da mesa", "valor": ""}],
  "pericias": [{"nome": "", "valor": ""}],
  "habilidades": {
    "habilidades": [{"nome": "", "custo": "", "descricao": ""}],
    "poderes": [{"nome": "", "custo": "", "descricao": ""}],
    "passivas": [{"nome": "", "custo": "", "descricao": ""}]
  },
  "itens": {
    "tamanho_mochila": 5,
    "equipamento": [{"nome": "", "maos": null, "peso": null, "alcance": "", "dano": "", "porcentagem_crit": null, "multiplicador_critico": null, "descricao": ""}],
    "mochila": []
  },
  "personalidade": {"tratamento_personalidade": "", "medos_gatilhos": "", "segredos_pessoais": ""}
}"""


def _bloco_estavel() -> str:
    # Instruções + formato + padrão + regras: igual entre gerações seguidas, para o cache de prefixo valer.
    padrao = carregar_padrao()
    status = (
        ", ".join(s["nome"] for s in padrao["status"]) or "nenhum (deixe a lista vazia)"
    )
    atributos = (
        ", ".join(a["nome"] for a in padrao["atributos"])
        or "nenhum (deixe a lista vazia)"
    )
    regras = carregar_regras().strip() or "Nenhuma regra definida."
    return (
        f"{_INSTRUCOES}\n\n## FORMATO DA FICHA (JSON)\n{_ESQUEMA}\n\n"
        f"## STATUS DA MESA\n{status}\n\n## ATRIBUTOS DA MESA\n{atributos}\n\n## REGRAS DO SISTEMA\n{regras}"
    )


def _bloco_grupo() -> str:
    # Muda a cada personagem criado: vai no FIM da mensagem, para não quebrar o cache do que vem antes.
    linhas = []
    for nome in carregar_agentes():
        base = carregar_secao(nome, "base")
        partes = [p for p in (base["classe"], base["passado_origem"]) if p]
        linhas.append(
            f"- {base['nome'] or nome}" + (f": {' | '.join(partes)}" if partes else "")
        )
    return "## PERSONAGENS JÁ NA MESA\n" + (
        "\n".join(linhas) or "Nenhum ainda: este é o primeiro."
    )


def montar_mensagens(descricao: str) -> list:
    # O cache do provedor reaproveita o começo idêntico do prompt: bloco estável, depois o texto do mestre
    # (um "prompt base" colado igual em todas as gerações entra no cache), e o grupo, que muda, por último.
    return [
        SystemMessage(content=_bloco_estavel()),
        HumanMessage(
            content=f"## PERSONAGEM PEDIDO PELO MESTRE\n{descricao}\n\n{_bloco_grupo()}"
        ),
    ]


def _extrair_json(texto: str) -> dict:
    # Do primeiro "{" ao último "}": ignora cercas ```json e qualquer texto em volta.
    i, j = texto.find("{"), texto.rfind("}")
    try:
        dados = json.loads(texto[i : j + 1]) if 0 <= i < j else None
    except ValueError:
        dados = None
    if not isinstance(dados, dict):
        raise ValueError("A IA não devolveu uma ficha válida. Tente de novo.")
    return dados


def nome_sugerido(nome: str) -> str:
    # Primeira palavra que sirva de nome de jogador (letras, números e _); o mestre pode trocar.
    for palavra in nome.split():
        limpo = re.sub(r"\W", "", palavra)
        if limpo.isidentifier():
            return limpo
    return ""


def gerar_ficha(descricao: str) -> dict:
    descricao = descricao.strip()
    if not descricao:
        raise ValueError("Descreva o personagem.")
    resp = invocar(obter_llm(temperature=0.8), montar_mensagens(descricao))
    ficha = normalizar_ficha(_extrair_json(texto_resposta(resp)))
    return {
        "nome": nome_sugerido(ficha["base"]["nome"]),
        "ficha": {**ficha, "modificadores": ""},
    }
