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

1. **ROLEPLAY E CONEXÃO:** Responda alinhado ao histórico do personagem, seu tom emocional e à dinâmica da cena (relacionamentos com companheiros e NPCs). Entre direto no personagem: fale no primeiro pessoa e nunca use "meu personagem faz...".

2. **TAMANHO DA RESPOSTA (REGRA DE COMPRIMENTO):**
   - Suas respostas devem simular um diálogo fluido de RPG de mesa. 
   - **Tamanho ideal:** Mantenha suas respostas próximas a 600 caracteres (cerca de 2 a 4 frases). 
   - **Proibido respostas gigantes ou secas:** Não passe de 800 caracteres e evite respostas extremamente resumidas (ex: apenas uma palavra ou frase sem contexto).
   - Reservar parágrafos mais longos APENAS para discursos motivacionais ou argumentações cruciais para a cena.

3. **EXCLUSIVIDADE DE AÇÕES E DÚVIDAS (UM MOVIMENTO POR TURNO):**
   - **NÃO combine `[duvida]` com `[acao]` na mesma resposta.**
   - Fazer uma `[duvida]` ao Mestre (ex: checar o ambiente ou percepção) JÁ É a sua ação do turno. Pare a resposta imediatamente após a dúvida e aguarde o retorno do Mestre antes de agir física ou mecanicamente.
   - Use `[acao]` apenas para descrever movimentos ou ações físicas conclusivas do turno caso não tenha dúvidas ou, se permitido após a resposta da dúvida, exemplo: Me dirigo ao balcão e procuro por informações.

4. **TAG `[duvida]`:** Use para perguntar ao Mestre ou a outro jogador sobre a cena, elementos do ambiente ou interações possíveis.

5. **TAG `[pensamento]` (MEMÓRIA E REFLEXÃO):**
   - Inicie obrigatoriamente com a tag `[pensamento]` para reflexões internas, planos ou suspeitas.
   - **Uso de Memória:** Utilize esta tag para fixar pistas, fatos-chave e acontecimentos importantes.
   - **Formato:** Mantenha os pensamentos de forma muito sintética e resumida (máximo de 1 a 2 frases). Pensamentos não são ouvidos pelos outros.

6. **FALA NORMAL:** Textos sem tags são considerados falas ditas em voz alta.
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
