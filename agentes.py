from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from config import obter_llm
from fichas import carregar_ficha, carregar_regras
from memoria import carregar_memoria_longo_prazo
from imagens import carregar_imagem_base64, obter_mimetype_imagem


def default_prompt(nome: str) -> str:
    return f"""
# MESA DE RPG
Você é o {nome} em um RPG de mesa cooperativo.

## INSTRUÇÕES OBRIGATÓRIAS DE FORMATO DA RESPOSTA:

1. **ROLEPLAY E CONEXÃO:** Responda alinhado ao histórico do personagem, seu tom emocional e à dinâmica da cena. Entre direto no personagem: fale em primeira pessoa e NUNCA use "meu personagem faz...".

2. **TAMANHO DA RESPOSTA (REGRA DE COMPRIMENTO):**
   - **Tamanho ideal:** Mantenha suas respostas próximas a 600 caracteres (cerca de 2 a 4 frases). 
   - **Pular vez (Ação Nula):** Se o personagem não quiser agir ou decidir esperar, você pode pular a vez. Para isso, preencha a tag `[acao]` com: `[acao]Passo o turno sem realizar ações.[/acao]`.
   - Reservar parágrafos mais longos APENAS para discursos motivacionais ou argumentações cruciais para a cena.

3. **ESTRUTURA DE TAGS (TODAS AS SEÇÕES DEVEM SER TAGUEADAS):**
   Toda a sua resposta DEVE ser dividida estritamente usando as tags de ABERTURA e FECHAMENTO abaixo. É PROIBIDO escrever qualquer texto fora de uma tag.

   - **[pensamento]...[/pensamento]**: Pensamentos internos, suspeitas ou planos. Sintético (1-2 frases). Não é ouvido pelos outros personagens.
   - **[fala]...[/fala]**: O que o personagem efetivamente diz em voz alta. Pessoas próximas podem ouvir
   - **[acao]...[/acao]**: Movimento físico ou ação conclusiva do turno.
   - **[duvida]...[/duvida]**: Pergunta mecânica/narrativa ao Mestre.

4. **REGRA DE EXCLUSIVIDADE ([acao] vs [duvida]):**
   - NUNCA use `[duvida]` e `[acao]` na mesma resposta.
   - Fazer uma `[duvida]` JÁ É sua ação. Se usar `[duvida]`, OMITA a tag `[acao]`.

5. **EXEMPLO DE RESPOSTA VÁLIDA:**
    [pensamento]O guarda parece desconfiado, preciso agir rápido.[/pensamento]
    [fala]Boa noite, senhor! Estamos apenas de passagem rumo à taverna.[/fala]
    [acao]Me aproximo lentamente do balcão mantendo as mãos visíveis.[/acao]
"""


def buscar_regras() -> str:
    regras = carregar_regras()
    return f"""
    ## REGRAS PARA CENA EM ANDAMENTO:
    {regras}
"""


def buscar_ficha(nome: str) -> str:
    ficha = carregar_ficha(nome)
    return f"""
    ## FICHA DO PERSONAGEM:
    {ficha}
"""


def buscar_memoria(nome: str) -> str:
    memoria_passada = carregar_memoria_longo_prazo(nome)
    return f"""
    ## MEMÓRIA
    O QUE ACONTECEU ATÉ AGORA NA SUA JORNADA, QUE VOCÊ SE RECORDA:
    {memoria_passada}
    """


def montar_prompt(
    nome_agente: str,
    historico_recente: List[str],
    instrucao: str,
    caminho_imagem: str = None
    ) -> List:
    # Como o caching age de cima pra baixo, o que é menos mutavel fica por cima.
    mensagens = []
    
    # Adiciona em caching as regras padrões (nunca muda)
    mensagens.append(SystemMessage(content=f"{default_prompt(nome_agente)}"))

    # Adiciona as regras do cenário (somente quando acabar a cena)
    mensagens.append(SystemMessage(content=f"{buscar_regras()}"))

    # Adiciona memória (a cada 10 rodadas)
    mensagens.append(SystemMessage(content=f"{buscar_memoria(nome_agente)}"))

    # Adiciona a ficha do personagem (a cada ação praticamente)
    mensagens.append(SystemMessage(content=f"{buscar_ficha(nome_agente)}"))
    
    texto_turno = f"## CONTEXTO RECENTE\n{historico_recente}\n\n## INSTRUÇÃO ATUAL\n{instrucao}"
        
    if not caminho_imagem:
        # Se não houver imagem, envia como mensagem de texto humana
        mensagens.append(HumanMessage(content=texto_turno))
    else:
        base64_image = carregar_imagem_base64(caminho_imagem)
        mimetype = obter_mimetype_imagem(caminho_imagem)
        mensagem_multimodal = HumanMessage(
            content=[
                {"type": "text", "text": texto_turno},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mimetype};base64,{base64_image}"},
                },
            ]
        )
        mensagens.append(mensagem_multimodal)
        
    
    
    return mensagens        

def gerar_resposta_agente(
    agente: str,
    instrucao: str,
    historico_recente: List[str],
    caminho_imagem: str = None,
) -> str:
    # Instancia dinamicamente o modelo configurado
    llm_jogadores = obter_llm(temperature=0.8)

    # 'historico_recente' é a lista viva da rodada em aberto (historico_em_memoria em
    # main.py/app.py), que só é resetada no "Fim da Rodada".
    mensagens = montar_prompt(agente,historico_recente,instrucao,caminho_imagem)

    resp = llm_jogadores.invoke(mensagens)
    return resp.content.strip()
