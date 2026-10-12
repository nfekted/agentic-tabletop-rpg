from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from rpg.config import carregar_agentes, carregar_configuracao, obter_llm
from rpg.fichas import carregar_ficha, carregar_regras
from rpg.memoria import carregar_memoria_longo_prazo
from rpg.limites import invocar
from rpg.metricas import registrar_chamada
from rpg.imagens import carregar_imagem_base64, obter_mimetype_imagem


def default_prompt() -> str:
    jogadores = ", ".join(carregar_agentes())
    return f"""
# MESA DE RPG
Você está em um RPG de mesa cooperativo.

## INSTRUÇÕES OBRIGATÓRIAS DE FORMATO DA RESPOSTA:

1. **ROLEPLAY E CONEXÃO:** Responda alinhado ao histórico do personagem, seu tom emocional e à dinâmica da cena. Entre direto no personagem: fale em primeira pessoa e NUNCA use "meu personagem faz...". Não use Emojis em nenhuma hipótese.

2. **ANTI META-GAMING (PROIBIÇÃO DE CONHECIMENTO EXTERNO):**
   - Aborde ESTRITAMENTE com base no que seu personagem presenciou, ouviu ou sabe.
   - É PROIBIDO agir, recuar ou falar usando como base informações no qual aconteceram em locais onde seu persoangem não estava, ou conhecimento não compartilhado por outros da sua equipe.
   
3. **TAMANHO DA RESPOSTA (REGRA DE COMPRIMENTO):**
   - **Tamanho ideal:** Mantenha suas respostas próximas a 600 caracteres (cerca de 2 a 4 frases). 
   - **Pular vez (Ação Nula):** Se o personagem não quiser agir ou decidir esperar, você pode pular a vez. Para isso, preencha a tag `[acao]` com: `[acao]Passo o turno sem realizar ações.[/acao]`.
   - Reservar parágrafos mais longos APENAS para discursos motivacionais ou argumentações cruciais para a cena.

4. **ESTRUTURA DE TAGS (TODAS AS SEÇÕES DEVEM SER TAGUEADAS):**
   Toda a sua resposta DEVE ser dividida estritamente usando as tags de ABERTURA e FECHAMENTO abaixo. É PROIBIDO escrever qualquer texto fora de uma tag.

   - **[pensamento]...[/pensamento]**: Pensamentos internos, suspeitas ou planos. Sintético (1-2 frases). Não é ouvido pelos outros personagens.
   - **[fala]...[/fala]**: O que o personagem efetivamente diz em voz alta. Pessoas próximas podem ouvir
   - **[acao]...[/acao]**: Movimento físico ou ação conclusiva do turno.
   - **[duvida]...[/duvida]**: Pergunta mecânica/narrativa ao Mestre (só ao Mestre).
   - **[chamar]NomeExato: o que você diz a ele[/chamar]**: Chama outro jogador da mesa para participar da cena (ex.: `[chamar]Fulano: Pode vir ver isso?[/chamar]`). Use SOMENTE um destes nomes, escritos exatamente assim: {jogadores}. Nunca chame a si mesmo. Chame apenas personagens próximos ou na mesma cena que você.
   
5. **AUTONOMIA DE SEGREDO E REVELAÇÃO:**
   - **Informações Privadas:** Fatos revelados em cenas privadas, visões ou pensamentos pertencem exclusivamente ao seu personagem.
   - **Decisão de Revelar:** Você tem total autonomia para decidir SE, QUANDO e COMO compartilhar um segredo. Se optar por manter em segredo, use `[pensamento]` ou minta em `[fala]`. Só compartilhe com o grupo se o personagem achar que é o momento certo e seguro.

6. **REGRA DE EXCLUSIVIDADE ([acao] / [duvida] / [chamar]):**
   - NUNCA use `[duvida]` junto com `[acao]` ou `[chamar]` na mesma resposta.
   - Fazer uma `[duvida]` JÁ É sua ação. Se usar `[duvida]`, OMITA as tags `[acao]` e `[chamar]`.
   - `[chamar]` pode acompanhar `[fala]` e `[acao]`.
   - Não é obrigatório usar todas tags em uma resposta, você pode só falar, só ter duvida, só agir, só pensar, só chamar e etc.

7. **EXEMPLO DE RESPOSTA VÁLIDA:**
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
    ## FICHA DO PERSONAGEM
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
    caminho_imagem: str = None,
) -> List:
    # o cache age de cima para baixo: o menos mutável vai primeiro
    mensagens = [
        SystemMessage(content=default_prompt()),
        SystemMessage(content=buscar_regras()),
        SystemMessage(content=buscar_memoria(nome_agente)),
        SystemMessage(content=buscar_ficha(nome_agente)),
    ]

    texto_turno = (
        f"## CONTEXTO RECENTE\n{historico_recente}\n\n## INSTRUÇÃO ATUAL\n{instrucao}"
    )

    if not caminho_imagem:
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
    llm_jogadores = obter_llm(temperature=0.8)

    # historico_recente: lista viva da rodada (sessao["historico"]), zerada no fim da rodada
    mensagens = montar_prompt(agente, historico_recente, instrucao, caminho_imagem)

    resp = invocar(llm_jogadores, mensagens)
    registrar_chamada(
        agente,
        mensagens,
        resp,
        carregar_configuracao().get("provedor", ""),
        bool(caminho_imagem),
    )
    return resp.content.strip()
