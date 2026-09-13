from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm_jogadores
from fichas import carregar_ficha, carregar_regras
from memoria import carregar_memoria_longo_prazo
from imagens import carregar_imagem_base64, obter_mimetype_imagem


def get_system_prompt(nome: str) -> str:
    ficha = carregar_ficha(nome)
    regras = carregar_regras()
    memoria_passada = carregar_memoria_longo_prazo(nome)
    return f"""Você é o {nome} em um RPG de mesa cooperativo.
REGRAS PARA CENA ATUAL:
{regras}

SUA FICHA/PERSONAGEM:
{ficha}

O QUE ACONTECEU ATÉ AGORA NA SUA JORNADA, QUE VOCÊ SE RECORDA:
{memoria_passada}

# INSTRUÇÕES OBRIGATÓRIAS DE FORMATO DA RESPOSTA:
1. Responda sempre alinhado ao histórico do personagem, seu tom emocional recente e a dinâmica da cena. Relações com companheiros e NPC's
2. Seja conciso. Suas respostas devem simular uma conversa onde cada um fala um pouco, limite-se a paragrafos maiores para discursos motivacionais, ou argumentação em uma cena caso extremamente necessário.
3. Use [acao] para descrever a ação física ou movimento final do turno conforme regras gerais.
4. Use [duvida] para perguntar a outro jogador, ou mestre, sobre alguma ação, cena ou iteração possível.
5. Para reflexões internas, planos ou suspeitas não ditos, inicie obrigatoriamente com a tag [pensamento]. Pensamentos não são ouvidos pelos outros."
6. Em caso de texto sem tags será considerado uma fala normal, podendo falar diretamente como o personagem sem por "meu personagem faz...", entre no roleplay.
"""


def gerar_resposta_agente(
    agente: str,
    instrucao: str,
    historico_recente: List[str],
    caminho_imagem: str = None,
) -> str:
    # 'historico_recente' é a lista viva da rodada em aberto (historico_em_memoria em
    # main.py/app.py), que só é resetada no "Fim da Rodada".
    contexto_visivel = "\n".join(historico_recente)

    prompt_texto = f"{get_system_prompt(agente)}\nContexto visível da cena:\n{contexto_visivel}\n\nInstrução atual: {instrucao}"

    if not caminho_imagem:
        resp = llm_jogadores.invoke([SystemMessage(content=prompt_texto)])
        return resp.content.strip()

    base64_image = carregar_imagem_base64(caminho_imagem)
    mimetype = obter_mimetype_imagem(caminho_imagem)

    mensagem_multimodal = HumanMessage(
        content=[
            {"type": "text", "text": prompt_texto},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mimetype};base64,{base64_image}"},
            },
        ]
    )

    resp = llm_jogadores.invoke([mensagem_multimodal])
    return resp.content.strip()
