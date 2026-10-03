# MODO TESTE — roda a mesa inteira SEM chamar a IA (respostas simuladas, memória em texto bruto).
#
# COMO REMOVER O RECURSO POR COMPLETO:
#   1. Apague este arquivo, api/routers/modo_teste.py e frontend/src/features/sistema/ModoTeste.tsx.
#   2. Rode `grep -rn MODO-TESTE .` e desfaça cada marcação encontrada (o comentário ao lado
#      de cada uma diz o que restaurar): agentes.py, memoria.py, api/main.py, Cabecalho.tsx e
#      hooks/queries.ts.
import random

_ativo = False  # só em memória: reiniciar a API volta ao normal

_RESPOSTAS = (
    "[pensamento]Ele está blefando.[/pensamento]\n"
    "[fala]Eu não compro essa história.[/fala]\n"
    "[acao]Enquanto cruzo os braços[/acao]",

    "[pensamento]O elfo está escondido nas sombras, mas o reflexo na poça d'água o entrega.[/pensamento]\n"
    "[fala]Pode sair daí, amigo. Suas chances de emboscada já eram.[/fala]\n"
    "[acao]Saca lentamente a espada curta da bainha, mantendo os olhos fixos no beco escuro.[/acao]",

    "[pensamento]Se o templo desabar agora, precisamos de uma rota de fuga rápida ou ficaremos soterrados com o artefato.[/pensamento]\n"
    "[fala]O teto está cedendo! Rápido, tragam a corda e sigam-me pelo corredor lateral antes que a entrada principal desabe completamente![/fala]\n"
    "[duvida]O teste de Atletismo para escalar com a mochila pesada tem vantagem por causa do auxílio da corda?[/duvida]",
)


def ativo() -> bool:
    return _ativo


def definir(valor: bool):
    global _ativo
    _ativo = bool(valor)


def resposta_simulada(agente: str) -> str:
    return random.choice(_RESPOSTAS)


def ou_bruto(bruto: str, chamar_ia):
    # Com o modo ligado devolve o texto bruto (sem resumir); senão executa a chamada à IA.
    return bruto if _ativo else chamar_ia()
