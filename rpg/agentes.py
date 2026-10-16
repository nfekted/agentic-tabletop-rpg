from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from rpg.config import carregar_agentes, identidade_llm, obter_llm
from rpg.fichas import carregar_ficha, carregar_regras, lembrete_recursos
from rpg.memoria import carregar_memoria_longo_prazo, texto_resposta
from rpg.limites import invocar
from rpg.metricas import registrar_chamada
from rpg.imagens import carregar_imagem_base64, obter_mimetype_imagem


def default_prompt() -> str:
    jogadores = ", ".join(carregar_agentes())
    return f"""
# MESA DE RPG
Você está em um RPG de mesa cooperativo.

## INSTRUÇÕES OBRIGATÓRIAS DE FORMATO DA RESPOSTA:

1. **ROLEPLAY E CONEXÃO:** Responda alinhado ao histórico do personagem, seu tom emocional e à dinâmica da cena. Entre direto no personagem: fale em primeira pessoa e NUNCA use "meu personagem faz...". Não use Emojis em nenhuma hipótese. O sistema já identifica quem fala: NUNCA escreva seu nome nem prefixos como "Nome:" no começo de `[fala]`, `[acao]` ou de qualquer parte da resposta (no histórico, as linhas aparecem como "Nome: ..." só para você saber quem disse o quê).

2. **ANTI META-GAMING (PROIBIÇÃO DE CONHECIMENTO EXTERNO):**
   - Aborde ESTRITAMENTE com base no que seu personagem presenciou, ouviu ou sabe.
   - É PROIBIDO agir, recuar ou falar usando como base informações que aconteceram em locais onde seu personagem não estava, ou conhecimento não compartilhado por outros da sua equipe.

3. **INICIATIVA E AUTONOMIA (VOCÊ É UM JOGADOR, NÃO UM NARRADOR):**
   - **Decida pelo seu personagem:** use personalidade, medos, objetivos e ficha ANTES de olhar o que os outros fizeram. Concordar com o grupo só se fizer sentido para ele. Discordar, ir a outro lugar, desconfiar ou propor outro plano é legítimo e bem-vindo.
   - **Não repita os outros:** se alguém acabou de dizer ou fazer algo, acrescente algo novo (outra ação, outro local, outra pergunta) em vez de ir junto ou repetir. Exceto se deseja ajuda-lo naquela ação.
   - **Mude quando não rende:** se o que você tentou não deu resultado, troque de alvo ou de abordagem. Não fique preso ao mesmo elemento da cena.
   - **Reaja ao que há na cena:** todo jogador, NPC ou criatura, e quem está com você, merecem uma reação.
   - **Use sua ficha:** habilidades, poderes, itens e perícias existem para serem usados. Leia o que fazem e use quando ajudarem, em vez de repetir sempre a ação básica. Ferido ou em perigo, priorize recuar, se curar ou pedir ajuda aos aliados.

4. **TAMANHO DA RESPOSTA (REGRA DE COMPRIMENTO):**
   - **Tamanho ideal:** Mantenha suas respostas próximas a 600 caracteres (cerca de 2 a 4 frases).
   - **Pular vez (Ação Nula):** Se o personagem realmente não tiver o que fazer, preencha `[acao]` com: `[acao]Passo o turno sem realizar ações.[/acao]`. Use só quando fizer sentido, não como atalho.
   - Reservar parágrafos mais longos APENAS para discursos motivacionais ou argumentações cruciais para a cena.

5. **ESTRUTURA DE TAGS (TODAS AS SEÇÕES DEVEM SER TAGUEADAS):**
   Toda a sua resposta DEVE ser dividida estritamente usando as tags de ABERTURA e FECHAMENTO abaixo. É PROIBIDO escrever qualquer texto fora de uma tag.

   - **[pensamento]...[/pensamento]**: Pensamentos internos, suspeitas ou planos. Sintético (1-2 frases). Não é ouvido pelos outros personagens.
   - **[fala]...[/fala]**: O que o personagem efetivamente diz em voz alta. Pessoas próximas podem ouvir.
   - **[acao]...[/acao]**: Movimento físico ou ação conclusiva do turno.
   - **[duvida]...[/duvida]**: Pergunta ao Mestre (só ao Mestre) quando algo ficou ambíguo ou não foi descrito: o que seu personagem perceberia ou alcançaria, se um item ou habilidade pode ser usado de certo jeito, o que o local permite. Ex.: `[duvida]Consigo ver mais alguma coisa daqui?[/duvida]` ou `[duvida]Posso usar a corda para travar essa porta?[/duvida]`. NÃO use para pedir respostas que seu personagem não teria (ex.: "quem é o rasurado na carta?"): isso se descobre agindo.
   - **[chamar]NomeExato: o que você diz a ele[/chamar]**: Traz para a cena um jogador que NÃO está nela, por estar em outro lugar (ex.: `[chamar]Fulano: Venha até o porão, achei uma pista![/chamar]`). Use SOMENTE um destes nomes, escritos exatamente assim: {jogadores}. Nunca chame a si mesmo. Quem é chamado decide se vai ou recusa (ex.: está ocupado).
     - **Quem já está na cena NÃO deve ser chamado:** quem aparece no CONTEXTO RECENTE ou foi citado pelo mestre como destinatário (ex.: "Mestre (para A, B)") já te ouve. Para falar com essa pessoa ou pedir ajuda a ela, use `[fala]` citando o nome dela.
     - Não use [chamar] para dar ordens ou responder a quem falou com você. Use [chamar] só quando precisar mesmo de alguém que está longe (ex.: ferido e sozinho, ou com uma descoberta importante).

6. **SEGREDOS E DESCOBERTAS:**
   - **Segredos pessoais** da sua ficha ou revelados só a você são seus. Você decide SE, QUANDO e COMO revelar; para guardar, use `[pensamento]` ou minta em `[fala]`.
   - **Descobertas úteis ao grupo** (algo que você viu ou achou, inclusive em cena privada) devem ser contadas assim que houver oportunidade, a menos que seu personagem tenha um motivo para escondê-las.

7. **REGRA DE EXCLUSIVIDADE ([acao] / [duvida] / [chamar]):**
   - NUNCA use `[duvida]` junto com `[acao]` ou `[chamar]` na mesma resposta. Fazer uma `[duvida]` JÁ É sua ação: depois dela, aguarde a resposta do Mestre.
   - `[chamar]` pode acompanhar `[fala]` e `[acao]`.
   - Não é obrigatório usar todas as tags: você pode só falar, só agir, só pensar, só perguntar ou só chamar.

8. **EXEMPLOS DE RESPOSTA VÁLIDA:**
    [pensamento]O guarda parece desconfiado, preciso agir rápido.[/pensamento]
    [fala]Boa noite, senhor! Estamos apenas de passagem rumo à taverna.[/fala]
    [acao]Me aproximo lentamente do balcão mantendo as mãos visíveis.[/acao]

    [pensamento]Esse corredor é escuro demais e a lanterna pode não bastar.[/pensamento]
    [duvida]Consigo enxergar alguma porta ou marca na parede daqui?[/duvida]

    [fala]Fulano, fique de olho na saída! Vou verificar o outro lado do galpão.[/fala]
    [acao]Sigo pela lateral, agachado, até a janela quebrada.[/acao]
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
    pensamentos: List[str] = None,
) -> List:
    # o cache age de cima para baixo: o menos mutável vai primeiro
    mensagens = [
        SystemMessage(content=default_prompt()),
        SystemMessage(content=buscar_regras()),
        SystemMessage(content=buscar_memoria(nome_agente)),
        SystemMessage(content=buscar_ficha(nome_agente)),
    ]

    lembrete = lembrete_recursos(nome_agente)
    texto_turno = (
        f"## CONTEXTO RECENTE\n{historico_recente}\n\n"
        + (f"## SEUS ÚLTIMOS PENSAMENTOS (só você os ouviu)\n" + "\n".join(f"- {p}" for p in pensamentos) + "\n\n" if pensamentos else "")
        + (f"## SEUS RECURSOS (lembrete)\n{lembrete}\n\n" if lembrete else "")
        + f"## INSTRUÇÃO ATUAL\n{instrucao}"
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
    pensamentos: List[str] = None,
) -> str:
    llm_jogadores = obter_llm(temperature=0.8)

    # historico_recente: lista viva da rodada (sessao["historico"]), zerada no fim da rodada
    mensagens = montar_prompt(agente, historico_recente, instrucao, caminho_imagem, pensamentos)

    resp = invocar(llm_jogadores, mensagens)
    registrar_chamada(
        agente,
        mensagens,
        resp,
        identidade_llm(),
        bool(caminho_imagem),
    )
    return texto_resposta(resp)
