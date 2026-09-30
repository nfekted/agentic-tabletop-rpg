# Persistência de memória por agente e a hierarquia rodada -> cena -> mesa.

import os
import re
import shutil
from typing import List
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from config import obter_llm
from fichas import carregar_arquivo
from tags import extrair_tags_resposta, formatar_conteudo_publico, formatar_para_autor


def obter_pasta_agente(agente: str) -> str:
    pasta = os.path.join("arquivos", f"memoria_{agente}")
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    return pasta


def _arquivos_numerados(pasta: str, prefixo: str) -> List[str]:
    # Lista "<prefixo>_N.txt" ordenada numericamente (rodada_2 antes de rodada_10).
    padrao = re.compile(rf"^{prefixo}_(\d+)\.txt$")
    achados = [(int(m.group(1)), f) for f in os.listdir(pasta) if (m := padrao.match(f))]
    return [f for _, f in sorted(achados)]


def _ler(caminho: str) -> str:
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def _texto_resp(resp) -> str:
    return str(getattr(resp, "content", resp)).strip()


def tamanho_memoria_chars(agente: str) -> int:
    # Total de caracteres da memória de longo prazo (mesa + cenas + rodadas).
    pasta = obter_pasta_agente(agente)
    total = len(carregar_arquivo(os.path.join(pasta, "mesa.txt"), ""))
    for prefixo in ("cena", "rodada"):
        for f in _arquivos_numerados(pasta, prefixo):
            total += len(_ler(os.path.join(pasta, f)))
    return total


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
    cenas = _arquivos_numerados(pasta, "cena")
    if cenas:
        memoria += "=== CENAS RECENTES ===\n"
        for c in cenas:
            caminho_c = os.path.join(pasta, c)
            with open(caminho_c, "r", encoding="utf-8") as f:
                memoria += f"[{c}]: " + f.read() + "\n"
        memoria += "\n"

    # 3. Lê as rodadas salvas
    rodadas = _arquivos_numerados(pasta, "rodada")
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

    rodadas = _arquivos_numerados(pasta, "rodada")
    cenas = _arquivos_numerados(pasta, "cena")

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
    def cancelar_rodada(motivo: str):
        # 1. Cria a pasta para rodadas canceladas se não existir
        pasta_canceladas = os.path.join("arquivos", "rodadas_canceladas")
        os.makedirs(pasta_canceladas, exist_ok=True)

        # 2. Formata a data atual
        data_formatada = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # 3. Varre as pastas dos agentes para buscar os arquivos temporários
        pasta_arquivos = "arquivos"
        if not os.path.exists(pasta_arquivos):
            return

        for subpasta in os.listdir(pasta_arquivos):
            caminho_agente = os.path.join(pasta_arquivos, subpasta)
            
            if os.path.isdir(caminho_agente) and subpasta.startswith("memoria_"):
                agente = subpasta.replace("memoria_", "")
                caminho_temp = os.path.join(caminho_agente, "rodada_atual_temp.txt")

                if os.path.exists(caminho_temp):
                    # Lê o conteúdo original
                    with open(caminho_temp, "r", encoding="utf-8") as f:
                        conteudo_original = f.read()

                    # Monta o cabeçalho no topo do arquivo
                    cabecalho = f"Rodada cancelada em {data_formatada}, motivo: {motivo}\n\n"
                    conteudo_final = cabecalho + conteudo_original

                    # Define o novo caminho e grava o arquivo cancelado
                    nome_arquivo_cancelado = f"rodada cancelada em {data_formatada}_{agente}.txt"
                    caminho_destino = os.path.join(pasta_canceladas, nome_arquivo_cancelado)

                    with open(caminho_destino, "w", encoding="utf-8") as f:
                        f.write(conteudo_final)

                    # Remove o temporário original
                    os.remove(caminho_temp)

    @staticmethod
    def finalizar_rodada(agentes_alvo: List[str]):
        # Consolida a rodada temporária em um resumo individual para cada agente alvo.
        for agente in agentes_alvo:
            pasta = obter_pasta_agente(agente)
            caminho_temp = os.path.join(pasta, "rodada_atual_temp.txt")

            if not os.path.exists(caminho_temp):
                continue

            rodadas_existentes = _arquivos_numerados(pasta, "rodada")
            num_rodada = len(rodadas_existentes) + 1

            with open(caminho_temp, "r", encoding="utf-8") as f:
                conteudo = f.read()

            mensagems = []
            
            prompt_base = f"""
            Você é o Historiador e Cronista oficial de uma mesa de RPG cooperativo.
            Sua missão é consolidar os acontecimentos da rodada recente em uma narrativa concisa, fluida e envolvente\n\n
            ## DIRETRIZES FUNDAMENTAIS DE SÍNTESE
            1. PENSAMENTOS INTERNOS ([pensamento]...[/pensamento]):
                - Sintetize pensamentos do personagem focado como suas intuições, sentimentos, reflexões ou segredos íntimos.".
                - NUNCA descreva um pensamento como algo que foi dito em voz alta ou percebido por outros personagens.
            2. FALAS E AÇÕES ([fala]...[/fala], [acao]...[/acao]):
                - Trate como os eventos reais, visíveis e audíveis que aconteceram na cena.
            3. DÚVIDAS ([duvida]...[/duvida]):
                - Trate como hesitações ou percepções atentas do personagem, sem incluir regras ou jargões mecânicos.
            4. TEXTO LIMPO E SEM TAGS:
                - É terminantemente PROIBIDO incluir as tags literais ([pensamento], [/pensamento], [fala], [acao], [duvida]) no resumo final.
                - Escreva uma prosa corrida fluida (2 a 4 frases ou parágrafos concisos) em terceira pessoa focada na personagem do resumo.
            """
        
            mensagems.append(SystemMessage(content=prompt_base))
            
            prompt_dinamico = f"""
            ## PERSONAGEM ALVO
            Foque a perspectiva e os sentimentos exclusivamente no personagem: {agente}.
            
            ## REGISTRO DA RODADA DE {agente}:
            {conteudo}
            
            CRÔNICA DA RODADA:
            """
            
            mensagems.append(HumanMessage(content=prompt_dinamico))

            llm_historiador = obter_llm(temperature=0.3)
            resumo = llm_historiador.invoke(mensagems).content.strip()

            nome_arq_rodada = os.path.join(pasta, f"rodada_{num_rodada}.txt")
            with open(nome_arq_rodada, "w", encoding="utf-8") as f:
                f.write(resumo)

            os.remove(caminho_temp)
            print(f"✅ Rodada {num_rodada} de {agente} encerrada e salva.")

            # Se atingir 10 rodadas na pasta deste agente, compila para Cena
            if num_rodada >= 10:
                GerenciadorMemoriaRPG.compilar_cenas(agente)

    @staticmethod
    def compilar_cenas(agente: str, encadear: bool = True):
        # Resume TODAS as rodadas existentes em uma cena. O automático chama com 10 rodadas;
        # a compressão manual chama com as que houver (encadear=False evita o ciclo automático).
        llm_historiador = obter_llm(temperature=0.3)
        pasta = obter_pasta_agente(agente)
        rodadas = _arquivos_numerados(pasta, "rodada")
        if not rodadas:
            return
        print(f"\n🔄 Compilando {len(rodadas)} rodada(s) em CENA para {agente}...")
        conteudo_rodadas = ""
        for nome_arq in rodadas:
            conteudo_rodadas += f"\n--- {nome_arq} ---\n" + _ler(os.path.join(pasta, nome_arq))

        prompt = f"""Sintetize estes resumos de rodadas da perspectiva de {agente} em uma narrativa fluida de CENA. Regras:
        Descarte:
        1. Saudações.
        2. Hesitações repetidas.
        3. Descrições redundantes
        4. Pensamentos que não alterem a decisão do personagem
        Foco:
        1. Ações concluidas
        2. Decisões tomadas
        3. Revelações importantes
        4. Novos perigos
        5. Pontos de virada.
        
        CENA:\n{conteudo_rodadas}"""
        resumo_cena = _texto_resp(llm_historiador.invoke(prompt))

        num_cena = len(_arquivos_numerados(pasta, "cena")) + 1
        nome_arq_cena = os.path.join(pasta, f"cena_{num_cena}.txt")

        with open(nome_arq_cena, "w", encoding="utf-8") as f:
            f.write(resumo_cena)

        for nome_arq in rodadas:
            os.remove(os.path.join(pasta, nome_arq))

        print(f"✅ {nome_arq_cena} criada com sucesso para {agente}!")

        if encadear and num_cena >= 10:
            GerenciadorMemoriaRPG.compilar_mesa(agente)

    @staticmethod
    def _resumir_cenas(agente: str):
        # Resume TODAS as cenas existentes. Retorna (resumo, lista de caminhos consumidos).
        llm_historiador = obter_llm(temperature=0.3)
        pasta = obter_pasta_agente(agente)
        caminhos = [os.path.join(pasta, f) for f in _arquivos_numerados(pasta, "cena")]
        if not caminhos:
            return "", []
        conteudo_cenas = ""
        for arq in caminhos:
            conteudo_cenas += f"\n--- {os.path.basename(arq)} ---\n" + _ler(arq)

        prompt = f"Faça um resumo consolidado destas cenas para o histórico de longo prazo de {agente}:\n{conteudo_cenas}"
        return _texto_resp(llm_historiador.invoke(prompt)), caminhos

    @staticmethod
    def _anexar_ao_mesa(pasta: str, resumo: str):
        caminho_mesa = os.path.join(pasta, "mesa.txt")
        historico_antigo = carregar_arquivo(caminho_mesa, "")
        texto_final = historico_antigo + "\n\n=== CAPÍTULO COMPILADO ===\n" + resumo
        with open(caminho_mesa, "w", encoding="utf-8") as f:
            f.write(texto_final)

    @staticmethod
    def compilar_mesa(agente: str):
        pasta = obter_pasta_agente(agente)
        print(f"\n📜 Compilando CENAS no histórico permanente de {agente}...")
        resumo_novo, caminhos = GerenciadorMemoriaRPG._resumir_cenas(agente)
        if not caminhos:
            return

        GerenciadorMemoriaRPG._anexar_ao_mesa(pasta, resumo_novo)

        for arq in caminhos:
            if os.path.exists(arq):
                os.remove(arq)

        print(f"🏛️ Histórico 'mesa.txt' de {agente} atualizado!")

    @staticmethod
    def _reduzir_mesa(agente: str, mesa: str, alvo_chars: int) -> str:
        # Pede ao agente historiador um resumo do mesa.txt com limite de caracteres.
        llm_historiador = obter_llm(temperature=0.3)

        def pedir(limite: int, aviso: str = "") -> str:
            prompt = f"""Você é o Historiador de uma mesa de RPG cooperativo. Reduza o histórico de longo prazo do personagem {agente} abaixo.
            Preserve nomes, decisões, revelações e consequências importantes; descarte detalhes secundários e repetições.
            Escreva em prosa corrida, em terceira pessoa, sem tags e sem títulos.
            O limite máximo de caracteres para esse resumo é de {limite} caracteres.{aviso}

            HISTÓRICO:
            {mesa}"""
            return _texto_resp(llm_historiador.invoke(prompt))

        resumo = pedir(int(alvo_chars * 0.9))
        if len(resumo) > alvo_chars:
            resumo = pedir(
                int(alvo_chars * 0.75),
                f"\n            ATENÇÃO: a tentativa anterior ficou com {len(resumo)} caracteres, acima do limite. Seja mais curto.",
            )
        return resumo

    @staticmethod
    def comprimir_memoria(agente: str):
        # Compressão manual: rodadas -> cena, reduz o mesa.txt e anexa o resumo das cenas.
        from config import carregar_configuracao
        from metricas import atualizar_apos_compressao

        pasta = obter_pasta_agente(agente)
        caminho_mesa = os.path.join(pasta, "mesa.txt")
        chars_antes = tamanho_memoria_chars(agente)
        if chars_antes == 0:
            return False, "Não há memória a comprimir."

        reducao = int(carregar_configuracao().get("alvo_reducao_pct") or 50)
        reducao = max(10, min(90, reducao))
        mesa_original = carregar_arquivo(caminho_mesa, "")
        caminho_bak = os.path.join(pasta, "mesa.bak")
        aviso = ""

        try:
            if mesa_original:
                shutil.copy2(caminho_mesa, caminho_bak)

            # 1. Rodadas -> cena (sem disparar o ciclo automático do mesa)
            GerenciadorMemoriaRPG.compilar_cenas(agente, encadear=False)

            # 2. Reduz o mesa.txt atual
            if mesa_original:
                alvo = int(len(mesa_original) * (1 - reducao / 100))
                reduzido = GerenciadorMemoriaRPG._reduzir_mesa(agente, mesa_original, alvo)
                if not reduzido:
                    raise ValueError("a LLM devolveu um resumo vazio")
                if len(reduzido) >= len(mesa_original):
                    raise ValueError("o resumo não ficou menor que o histórico original")
                if len(reduzido) > alvo:
                    aviso = f" (o histórico antigo ficou com {len(reduzido)} caracteres, acima do alvo de {alvo})"
                with open(caminho_mesa, "w", encoding="utf-8") as f:
                    f.write(reduzido)

            # 3. Resume as cenas e anexa ao mesa.txt já reduzido
            resumo_cenas, caminhos = GerenciadorMemoriaRPG._resumir_cenas(agente)
            if caminhos:
                GerenciadorMemoriaRPG._anexar_ao_mesa(pasta, resumo_cenas)
                for arq in caminhos:
                    if os.path.exists(arq):
                        os.remove(arq)
        except Exception as e:
            if mesa_original and os.path.exists(caminho_bak):
                shutil.copy2(caminho_bak, caminho_mesa)
            return False, f"Falha ao comprimir a memória: {e}"

        atualizar_apos_compressao(agente, chars_antes, tamanho_memoria_chars(agente))
        return True, f"Memória de {agente} comprimida{aviso}."
