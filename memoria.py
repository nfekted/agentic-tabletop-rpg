# Persistência de memória por agente e a hierarquia rodada -> cena -> mesa.

import os
from typing import List

from config import llm_historiador
from fichas import carregar_arquivo
from tags import extrair_tags_resposta, formatar_conteudo_publico, formatar_para_autor


def obter_pasta_agente(agente: str) -> str:
    pasta = os.path.join("arquivos", f"memoria_{agente}")
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    return pasta


def carregar_memoria_longo_prazo(agente: str) -> str:
    # Carrega a memória de longo prazo específica do diretório do agente.
    pasta = obter_pasta_agente(agente)
    memoria = ""

    # 1. Lê o histórico permanente (mesa.txt)
    caminho_mesa = os.path.join(pasta, "mesa.txt")
    if os.path.exists(caminho_mesa):
        with open(caminho_mesa, "r", encoding="utf-8") as f:
            memoria += "=== HISTÓRICO PERMANENTE DA MESA ===\n" + f.read() + "\n\n"

    # 2. Lê as cenas já concluídas
    cenas = sorted(
        [f for f in os.listdir(pasta) if f.startswith("cena_") and f.endswith(".txt")]
    )
    if cenas:
        memoria += "=== CENAS RECENTES ===\n"
        for c in cenas:
            caminho_c = os.path.join(pasta, c)
            with open(caminho_c, "r", encoding="utf-8") as f:
                memoria += f"[{c}]: " + f.read() + "\n"
        memoria += "\n"

    # 3. Lê as rodadas salvas
    rodadas = sorted(
        [
            f
            for f in os.listdir(pasta)
            if f.startswith("rodada_")
            and f.endswith(".txt")
            and f != "rodada_atual_temp.txt"
        ]
    )
    if rodadas:
        memoria += "=== ÚLTIMAS RODADAS ===\n"
        for r in rodadas:
            caminho_r = os.path.join(pasta, r)
            with open(caminho_r, "r", encoding="utf-8") as f:
                memoria += f"[{r}]: " + f.read() + "\n"

    return (
        memoria
        if memoria
        else "A aventura está apenas começando. Nenhuma rodada anterior registrada."
    )


def obter_arquivos_memoria(agente: str) -> dict:
    # Retorna, de forma estruturada, todo o conteúdo de memória de um agente
    pasta = obter_pasta_agente(agente)

    caminho_temp = os.path.join(pasta, "rodada_atual_temp.txt")
    temp = carregar_arquivo(caminho_temp, "")

    rodadas = sorted(
        f
        for f in os.listdir(pasta)
        if f.startswith("rodada_")
        and f.endswith(".txt")
        and f != "rodada_atual_temp.txt"
    )
    cenas = sorted(
        f for f in os.listdir(pasta) if f.startswith("cena_") and f.endswith(".txt")
    )

    return {
        "rodada_atual": temp,
        "rodadas": [(r, carregar_arquivo(os.path.join(pasta, r))) for r in rodadas],
        "cenas": [(c, carregar_arquivo(os.path.join(pasta, c))) for c in cenas],
        "mesa": carregar_arquivo(os.path.join(pasta, "mesa.txt"), ""),
    }


class GerenciadorMemoriaRPG:
    @staticmethod
    def salvar_log_rodada_atual(texto: str, agentes_alvo: List[str]):
        # Grava a linha de log do turno temporário na pasta dos agentes alvo.
        for agente in agentes_alvo:
            pasta = obter_pasta_agente(agente)
            caminho_temp = os.path.join(pasta, "rodada_atual_temp.txt")
            with open(caminho_temp, "a", encoding="utf-8") as f:
                f.write(texto + "\n")

    @staticmethod
    def salvar_resposta_agente(
        agente_autor: str,
        resposta: str,
        agentes_presentes: List[str],
    ):
        """
        Salva a resposta do agente com isolamento estrito de pensamentos:
        - Na pasta do próprio autor: salva tudo (pensamento + fala + acao/duvida).
        - Na pasta dos outros presentes na cena: salva APENAS o conteúdo público (fala + acao/duvida),
          garantindo que pensamentos nunca vazem para a memória dos companheiros.
        """
        tags = extrair_tags_resposta(resposta)
        conteudo_autor = formatar_para_autor(tags) or resposta
        conteudo_publico = formatar_conteudo_publico(tags)

        # 1. Registra na memória do autor (com pensamentos íntimos)
        if agente_autor in agentes_presentes:
            pasta_autor = obter_pasta_agente(agente_autor)
            caminho_temp_autor = os.path.join(pasta_autor, "rodada_atual_temp.txt")
            with open(caminho_temp_autor, "a", encoding="utf-8") as f:
                f.write(f"{agente_autor}: {conteudo_autor}\n")

        # 2. Registra na memória dos outros presentes (somente conteúdo público)
        if conteudo_publico:
            for outro in agentes_presentes:
                if outro != agente_autor:
                    pasta_outro = obter_pasta_agente(outro)
                    caminho_temp_outro = os.path.join(
                        pasta_outro, "rodada_atual_temp.txt"
                    )
                    with open(caminho_temp_outro, "a", encoding="utf-8") as f:
                        f.write(f"{agente_autor}: {conteudo_publico}\n")

    @staticmethod
    def limpar_temp_nao_envolvidos(agentes_nao_envolvidos: List[str]):
        # Remove o rodada_atual_temp.txt de agentes que não participaram da rodada.
        for agente in agentes_nao_envolvidos:
            pasta = obter_pasta_agente(agente)
            caminho_temp = os.path.join(pasta, "rodada_atual_temp.txt")
            if os.path.exists(caminho_temp):
                os.remove(caminho_temp)

    @staticmethod
    def finalizar_rodada(agentes_alvo: List[str]):
        # Consolida a rodada temporária em um resumo individual para cada agente alvo.
        for agente in agentes_alvo:
            pasta = obter_pasta_agente(agente)
            caminho_temp = os.path.join(pasta, "rodada_atual_temp.txt")

            if not os.path.exists(caminho_temp):
                continue

            rodadas_existentes = [
                f
                for f in os.listdir(pasta)
                if f.startswith("rodada_")
                and f.endswith(".txt")
                and f != "rodada_atual_temp.txt"
            ]
            num_rodada = len(rodadas_existentes) + 1

            with open(caminho_temp, "r", encoding="utf-8") as f:
                conteudo = f.read()

            prompt = f"""Você é o Historiador e Cronista oficial de uma mesa de RPG cooperativo.
Sua missão é consolidar os acontecimentos da rodada recente em uma narrativa concisa, fluida e envolvente da perspectiva do personagem: {agente}.

DIRETRIZES FUNDAMENTAIS DE SÍNTESE:
1. PENSAMENTOS INTERNOS ([pensamento]...[/pensamento]):
   - Se pertencerem a {agente}, sintetize como suas intuições, sentimentos, reflexões ou segredos íntimos.
   - NUNCA descreva um pensamento como algo que foi dito em voz alta ou percebido por outros personagens.
2. FALAS E AÇÕES ([fala]...[/fala], [acao]...[/acao]):
   - Trate como os eventos reais, visíveis e audíveis que aconteceram na cena.
3. DÚVIDAS ([duvida]...[/duvida]):
   - Trate como hesitações ou percepções atentas do personagem, sem incluir regras ou jargões mecânicos.
4. TEXTO LIMPO E SEM TAGS:
   - É terminantemente PROIBIDO incluir as tags literais ([pensamento], [/pensamento], [fala], [acao], [duvida]) no resumo final.
   - Escreva uma prosa corrida fluida (2 a 4 frases ou parágrafos concisos) em terceira pessoa focada em {agente}.

REGISTRO DA RODADA DE {agente}:
{conteudo}

CRÔNICA DA RODADA:"""
            resumo = llm_historiador.invoke(prompt).content.strip()

            nome_arq_rodada = os.path.join(pasta, f"rodada_{num_rodada}.txt")
            with open(nome_arq_rodada, "w", encoding="utf-8") as f:
                f.write(resumo)

            os.remove(caminho_temp)
            print(f"✅ Rodada {num_rodada} de {agente} encerrada e salva.")

            # Se atingir 10 rodadas na pasta deste agente, compila para Cena
            if num_rodada >= 10:
                GerenciadorMemoriaRPG.compilar_cenas(agente)

    @staticmethod
    def compilar_cenas(agente: str):
        pasta = obter_pasta_agente(agente)
        print(f"\n🔄 10 Rodadas atingidas para {agente}! Compilando CENA...")
        conteudo_rodadas = ""
        arquivos_rodadas = [
            os.path.join(pasta, f"rodada_{i}.txt") for i in range(1, 11)
        ]

        for arq in arquivos_rodadas:
            if os.path.exists(arq):
                with open(arq, "r", encoding="utf-8") as f:
                    conteudo_rodadas += (
                        f"\n--- {os.path.basename(arq)} ---\n" + f.read()
                    )

        prompt = f"Sintetize estes resumos de rodadas da perspectiva de {agente} em uma narrativa fluida de CENA:\n{conteudo_rodadas}"
        resumo_cena = llm_historiador.invoke(prompt).content.strip()

        cenas_existentes = [
            f for f in os.listdir(pasta) if f.startswith("cena_") and f.endswith(".txt")
        ]
        num_cena = len(cenas_existentes) + 1
        nome_arq_cena = os.path.join(pasta, f"cena_{num_cena}.txt")

        with open(nome_arq_cena, "w", encoding="utf-8") as f:
            f.write(resumo_cena)

        for arq in arquivos_rodadas:
            if os.path.exists(arq):
                os.remove(arq)

        print(f"✅ {nome_arq_cena} criada com sucesso para {agente}!")

        if num_cena >= 10:
            GerenciadorMemoriaRPG.compilar_mesa(agente)

    @staticmethod
    def compilar_mesa(agente: str):
        pasta = obter_pasta_agente(agente)
        print(f"\n📜 10 Cenas atingidas para {agente}! Compilando MESA permanente...")
        conteudo_cenas = ""
        arquivos_cenas = [os.path.join(pasta, f"cena_{i}.txt") for i in range(1, 11)]

        for arq in arquivos_cenas:
            if os.path.exists(arq):
                with open(arq, "r", encoding="utf-8") as f:
                    conteudo_cenas += f"\n--- {os.path.basename(arq)} ---\n" + f.read()

        prompt = f"Faça um resumo consolidado destas 10 cenas para o histórico de longo prazo de {agente}:\n{conteudo_cenas}"
        resumo_novo = llm_historiador.invoke(prompt).content.strip()

        caminho_mesa = os.path.join(pasta, "mesa.txt")
        historico_antigo = carregar_arquivo(caminho_mesa, "")
        texto_final = (
            historico_antigo + f"\n\n=== CAPÍTULO COMPILADO ===\n" + resumo_novo
        )

        with open(caminho_mesa, "w", encoding="utf-8") as f:
            f.write(texto_final)

        for arq in arquivos_cenas:
            if os.path.exists(arq):
                os.remove(arq)

        print(f"🏛️ Histórico 'mesa.txt' de {agente} atualizado!")
