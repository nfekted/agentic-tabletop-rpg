# Memória por agente: rodada -> cena -> mesa.
import os
import re
import shutil
from typing import List
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from rpg.config import carregar_configuracao, obter_llm
from rpg.fichas import carregar_arquivo
from rpg.limites import invocar
from rpg.metricas import atualizar_apos_compressao
from rpg.tags import extrair_tags_resposta, formatar_conteudo_publico, formatar_para_autor
from rpg.paths import ARQUIVOS


def obter_pasta_agente(agente: str) -> str:
    pasta = os.path.join(ARQUIVOS, f"memoria_{agente}")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _caminho_temp(agente: str) -> str:
    return os.path.join(obter_pasta_agente(agente), "rodada_atual_temp.txt")


def tamanho_rodada_atual(agente: str) -> int:
    # Caracteres já gravados na rodada em andamento deste personagem (o que o historiador vai resumir).
    return len(carregar_arquivo(_caminho_temp(agente)))


def _anexar_temp(agente: str, linha: str):
    with open(_caminho_temp(agente), "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _arquivos_numerados(pasta: str, prefixo: str) -> List[str]:
    # Lista "<prefixo>_N.txt" ordenada numericamente (rodada_2 antes de rodada_10).
    padrao = re.compile(rf"^{prefixo}_(\d+)\.txt$")
    achados = [(int(m.group(1)), f) for f in os.listdir(pasta) if (m := padrao.match(f))]
    return [f for _, f in sorted(achados)]


def _ler(caminho: str) -> str:
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def _invocar(llm, prompt):
    return invocar(llm, prompt)


def texto_resposta(resp) -> str:
    # Alguns modelos (ex.: Gemini 3) devolvem content como lista de blocos; fica só o texto, sem o "thinking".
    conteudo = getattr(resp, "content", resp)
    if isinstance(conteudo, list):
        partes = [
            p if isinstance(p, str) else p.get("text", "") if isinstance(p, dict) and p.get("type", "text") == "text" else ""
            for p in conteudo
        ]
        conteudo = "".join(partes)
    return str(conteudo).strip()


_RE_TAG_ABERTA = re.compile(r"\[/?(?:pensamento|fala|acao|duvida|chamar)\]", re.IGNORECASE)
_TAGS_EM_TEXTO = {
    "pensamento": "pensou, sem dizer em voz alta: ",
    "fala": "disse em voz alta: ",
    "acao": "fez: ",
    "duvida": "perguntou ao mestre: ",
    "chamar": "chamou em voz alta: ",
}


_FATOS_A_PRESERVAR = """- Nomes próprios: personagens, NPCs, cidade, locais, organizações. Nunca troque um nome por "a cidade", "o veterano" ou "a policial": use o nome.
        - A situação inicial e o objetivo da missão, mesmo que venham das primeiras rodadas.
        - Informações recebidas, pistas, descobertas, itens, decisões tomadas e promessas feitas.
        - Relações e tensões entre personagens e NPCs, e perigos ainda em aberto."""


def tags_para_texto(registro: str) -> str:
    # O historiador lê o registro sem as tags, para não ter o que copiar para o resumo.
    def trocar(m):
        return _TAGS_EM_TEXTO[m.group(1).lower()] + m.group(2).strip()

    return re.sub(r"\[(pensamento|fala|acao|duvida|chamar)\](.*?)\[/\1\]", trocar, registro, flags=re.DOTALL | re.IGNORECASE)


def limpar_tags(texto: str) -> str:
    # Garantia final: tags que o modelo copiou para o resumo são removidas, o conteúdo fica.
    return _RE_TAG_ABERTA.sub("", texto).strip()


def tamanho_memoria_chars(agente: str) -> int:
    # Total de caracteres da memória de longo prazo (mesa + cenas + rodadas).
    pasta = obter_pasta_agente(agente)
    total = len(carregar_arquivo(os.path.join(pasta, "mesa.txt"), ""))
    for prefixo in ("cena", "rodada"):
        for f in _arquivos_numerados(pasta, prefixo):
            total += len(_ler(os.path.join(pasta, f)))
    return total


def carregar_memoria_longo_prazo(agente: str) -> str:
    pasta = obter_pasta_agente(agente)
    memoria = ""

    caminho_mesa = os.path.join(pasta, "mesa.txt")
    if os.path.exists(caminho_mesa):
        memoria += "=== HISTÓRICO PERMANENTE DA MESA ===\n" + _ler(caminho_mesa) + "\n\n"

    cenas = _arquivos_numerados(pasta, "cena")
    if cenas:
        memoria += "=== CENAS RECENTES ===\n"
        for c in cenas:
            memoria += f"[{c}]: " + _ler(os.path.join(pasta, c)) + "\n"
        memoria += "\n"

    rodadas = _arquivos_numerados(pasta, "rodada")
    if rodadas:
        memoria += "=== ÚLTIMAS RODADAS ===\n"
        for r in rodadas:
            memoria += f"[{r}]: " + _ler(os.path.join(pasta, r)) + "\n"

    return memoria or "A aventura está apenas começando. Nenhuma rodada anterior registrada."


def obter_arquivos_memoria(agente: str) -> dict:
    pasta = obter_pasta_agente(agente)
    rodadas = _arquivos_numerados(pasta, "rodada")
    cenas = _arquivos_numerados(pasta, "cena")

    return {
        "rodada_atual": carregar_arquivo(_caminho_temp(agente), ""),
        "rodadas": [(r, carregar_arquivo(os.path.join(pasta, r))) for r in rodadas],
        "cenas": [(c, carregar_arquivo(os.path.join(pasta, c))) for c in cenas],
        "mesa": carregar_arquivo(os.path.join(pasta, "mesa.txt"), ""),
    }


class GerenciadorMemoriaRPG:
    @staticmethod
    def salvar_log_rodada_atual(texto: str, agentes_alvo: List[str]):
        for agente in agentes_alvo:
            _anexar_temp(agente, texto)

    @staticmethod
    def salvar_resposta_agente(
        agente_autor: str,
        resposta: str,
        agentes_presentes: List[str],
    ):
        tags = extrair_tags_resposta(resposta)
        conteudo_autor = formatar_para_autor(tags) or resposta
        conteudo_publico = formatar_conteudo_publico(tags)

        # o autor registra também os pensamentos; os demais, só o conteúdo público
        if agente_autor in agentes_presentes:
            _anexar_temp(agente_autor, f"{agente_autor}: {conteudo_autor}")
        if conteudo_publico:
            for outro in agentes_presentes:
                if outro != agente_autor:
                    _anexar_temp(outro, f"{agente_autor}: {conteudo_publico}")

    @staticmethod
    def substituir_trecho_temp(trecho: str, novo: str, agentes: List[str]):
        # Troca a última ocorrência de `trecho` na memória da rodada atual de cada agente.
        for agente in agentes:
            caminho = _caminho_temp(agente)
            if not os.path.exists(caminho):
                continue
            texto = _ler(caminho)
            i = texto.rfind(trecho)
            if i < 0:
                continue
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto[:i] + novo + texto[i + len(trecho):])

    @staticmethod
    def limpar_temp_nao_envolvidos(agentes_nao_envolvidos: List[str]):
        for agente in agentes_nao_envolvidos:
            caminho_temp = _caminho_temp(agente)
            if os.path.exists(caminho_temp):
                os.remove(caminho_temp)

    @staticmethod
    def cancelar_rodada(motivo: str):
        pasta_canceladas = os.path.join(ARQUIVOS, "rodadas_canceladas")
        os.makedirs(pasta_canceladas, exist_ok=True)
        data_formatada = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        for subpasta in os.listdir(ARQUIVOS):
            caminho_agente = os.path.join(ARQUIVOS, subpasta)
            if os.path.isdir(caminho_agente) and subpasta.startswith("memoria_"):
                agente = subpasta.replace("memoria_", "")
                caminho_temp = os.path.join(caminho_agente, "rodada_atual_temp.txt")

                if os.path.exists(caminho_temp):
                    cabecalho = f"Rodada cancelada em {data_formatada}, motivo: {motivo}\n\n"
                    caminho_destino = os.path.join(
                        pasta_canceladas, f"rodada cancelada em {data_formatada}_{agente}.txt"
                    )
                    with open(caminho_destino, "w", encoding="utf-8") as f:
                        f.write(cabecalho + _ler(caminho_temp))
                    os.remove(caminho_temp)

    @staticmethod
    def finalizar_rodada(agentes_alvo: List[str]):
        for agente in agentes_alvo:
            GerenciadorMemoriaRPG.finalizar_rodada_agente(agente)

    @staticmethod
    def finalizar_rodada_agente(agente: str, gate=None):
        # Consolida a rodada temporária de um agente em um resumo e, se couber, a cascata cena -> mesa.
        # Cada passo só roda se ainda for necessário, então a fila pode retomar de onde parou após uma falha.
        # `gate(etapa)` é chamado antes de cada chamada à LLM ("rodada", "cena" ou "mesa").
        gate = gate or (lambda etapa: None)
        pasta = obter_pasta_agente(agente)
        caminho_temp = _caminho_temp(agente)

        if os.path.exists(caminho_temp):
            gate("rodada")
            rodadas_existentes = _arquivos_numerados(pasta, "rodada")
            num_rodada = len(rodadas_existentes) + 1

            conteudo = tags_para_texto(_ler(caminho_temp))
            alvo_chars = min(3500, max(1000, int(len(conteudo) * 0.4)))

            mensagems = []

            prompt_base = f"""
            Você é o Historiador e Cronista oficial de uma mesa de RPG cooperativo.
            Sua missão é consolidar os acontecimentos da rodada recente em uma crônica fiel, fluida e SEM PERDA DE FATOS,
            porque este texto será a única memória que o personagem terá desta rodada.

            ## FATOS QUE NUNCA PODEM SER PERDIDOS
            - Nomes próprios: personagens, NPCs, cidade, locais, organizações. Nunca troque um nome por "a cidade", "o veterano" ou "a policial": use o nome.
            - A situação inicial e a introdução narrada pelo mestre: onde estavam, como chegaram, quem os acompanhava.
            - O objetivo da missão e as regras ou condições dadas a eles.
            - Informações recebidas, pistas, descobertas, itens, decisões tomadas e promessas feitas.
            - Relações e tensões entre personagens e NPCs.
            Corte apenas repetições e detalhes sem consequência.

            ## COMO LER O REGISTRO
            - "pensou, sem dizer em voz alta": é íntimo do personagem. Resuma como intuição, sentimento ou plano dele e NUNCA como algo dito ou percebido por outros.
            - "disse em voz alta", "fez", "chamou em voz alta": eventos reais, visíveis e audíveis na cena.
            - "perguntou ao mestre": trate como hesitação ou atenção do personagem, sem jargão de regras.
            - Falas do Mestre e de NPCs são o mundo da história: preserve o que revelam.

            ## FORMATO
            - Prosa corrida em terceira pessoa, focada no personagem do resumo, em parágrafos curtos.
            - Tamanho: cerca de {alvo_chars} caracteres. Pode passar um pouco se for necessário para não perder fatos.
            - Não use tags, colchetes, listas nem marcações. Não invente nada que não esteja no registro.
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
            resumo = limpar_tags(texto_resposta(_invocar(llm_historiador, mensagems)))

            nome_arq_rodada = os.path.join(pasta, f"rodada_{num_rodada}.txt")
            with open(nome_arq_rodada, "w", encoding="utf-8") as f:
                f.write(resumo)

            os.remove(caminho_temp)
            print(f"Rodada {num_rodada} de {agente} encerrada e salva.")

        if len(_arquivos_numerados(pasta, "rodada")) >= 10:
            gate("cena")
            GerenciadorMemoriaRPG.compilar_cenas(agente, encadear=False)

        if len(_arquivos_numerados(pasta, "cena")) >= 10:
            gate("mesa")
            GerenciadorMemoriaRPG.compilar_mesa(agente)

    @staticmethod
    def compilar_cenas(agente: str, encadear: bool = True):
        # resume todas as rodadas existentes em uma cena (encadear=False evita o ciclo automático do mesa)
        llm_historiador = obter_llm(temperature=0.3)
        pasta = obter_pasta_agente(agente)
        rodadas = _arquivos_numerados(pasta, "rodada")
        if not rodadas:
            return
        print(f"\nCompilando {len(rodadas)} rodada(s) em CENA para {agente}...")
        conteudo_rodadas = "".join(f"\n--- {nome_arq} ---\n" + _ler(os.path.join(pasta, nome_arq)) for nome_arq in rodadas)

        alvo_chars = min(10000, max(2000, int(len(conteudo_rodadas) * 0.4)))
        prompt = f"""Você é o Historiador de uma mesa de RPG cooperativo. Sintetize estes resumos de rodadas, da perspectiva de {agente}, em uma narrativa fluida de CENA.
        Este texto substituirá as rodadas na memória do personagem, então NÃO PERCA FATOS.

        ## FATOS QUE NUNCA PODEM SER PERDIDOS
        {_FATOS_A_PRESERVAR}

        ## DESCARTE
        Saudações, hesitações repetidas, descrições redundantes e pensamentos que não alterem a decisão do personagem.

        ## FORMATO
        Prosa corrida em terceira pessoa, em ordem cronológica, sem tags, listas ou títulos. Cerca de {alvo_chars} caracteres; pode passar um pouco se for preciso para não perder fatos.

        CENA:\n{conteudo_rodadas}"""
        resumo_cena = limpar_tags(texto_resposta(_invocar(llm_historiador, prompt)))

        num_cena = len(_arquivos_numerados(pasta, "cena")) + 1
        nome_arq_cena = os.path.join(pasta, f"cena_{num_cena}.txt")

        with open(nome_arq_cena, "w", encoding="utf-8") as f:
            f.write(resumo_cena)

        for nome_arq in rodadas:
            os.remove(os.path.join(pasta, nome_arq))

        print(f"{nome_arq_cena} criada com sucesso para {agente}!")

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
        conteudo_cenas = "".join(f"\n--- {os.path.basename(arq)} ---\n" + _ler(arq) for arq in caminhos)

        alvo_chars = min(25000, max(4000, int(len(conteudo_cenas) * 0.4)))
        prompt = f"""Você é o Historiador de uma mesa de RPG cooperativo. Faça um resumo consolidado destas cenas para o histórico de longo prazo de {agente}.
        Este texto substituirá as cenas na memória do personagem, então NÃO PERCA FATOS.

        ## FATOS QUE NUNCA PODEM SER PERDIDOS
        {_FATOS_A_PRESERVAR}

        ## FORMATO
        Prosa corrida em terceira pessoa, em ordem cronológica, sem tags, listas ou títulos. Cerca de {alvo_chars} caracteres; pode passar um pouco se for preciso para não perder fatos.

        CENAS:\n{conteudo_cenas}"""
        return limpar_tags(texto_resposta(_invocar(llm_historiador, prompt))), caminhos

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
        print(f"\nCompilando CENAS no histórico permanente de {agente}...")
        resumo_novo, caminhos = GerenciadorMemoriaRPG._resumir_cenas(agente)
        if not caminhos:
            return

        GerenciadorMemoriaRPG._anexar_ao_mesa(pasta, resumo_novo)

        for arq in caminhos:
            if os.path.exists(arq):
                os.remove(arq)

        print(f"Histórico 'mesa.txt' de {agente} atualizado!")

    @staticmethod
    def encerrar_memoria(agente: str):
        # Fim de missão: rodadas -> cena -> mesa.txt (cada passo só roda se houver o que compilar).
        pasta = obter_pasta_agente(agente)
        if _arquivos_numerados(pasta, "rodada"):
            GerenciadorMemoriaRPG.compilar_cenas(agente, encadear=False)
        if _arquivos_numerados(pasta, "cena"):
            GerenciadorMemoriaRPG.compilar_mesa(agente)

    @staticmethod
    def resumir_missao(agente: str) -> str:
        # Resumo da missão como "passado do personagem", a partir do mesa.txt. Vazio se não há histórico.
        pasta = obter_pasta_agente(agente)
        mesa = carregar_arquivo(os.path.join(pasta, "mesa.txt"), "").strip()
        if not mesa:
            return ""
        alvo_chars = min(2500, max(600, int(len(mesa) * 0.15)))
        prompt = f"""Você é o Historiador de uma mesa de RPG cooperativo. A missão de {agente} terminou. Escreva o que ficará na ficha dele como PASSADO: um resumo da missão do ponto de vista dele.

        ## O QUE ENTRA
        Só os acontecimentos principais: onde e por que a missão começou, o objetivo, as grandes reviravoltas, quem morreu ou se perdeu, o que foi descoberto (ex.: o ponto fraco de um inimigo), o que os inimigos planejavam, como terminou e o que ficou em aberto.
        Mantenha os nomes próprios (pessoas, locais, organizações). Corte detalhes, diálogos e cenas sem consequência.

        ## FORMATO
        Prosa corrida em terceira pessoa, em tempo passado, como a lembrança de algo que já aconteceu. Cerca de {alvo_chars} caracteres, no máximo. Sem tags, listas, títulos ou marcações. Não invente nada que não esteja no histórico.

        HISTÓRICO DA MISSÃO:
        {mesa}"""
        return limpar_tags(texto_resposta(_invocar(obter_llm(temperature=0.3), prompt)))

    @staticmethod
    def _reduzir_mesa(agente: str, mesa: str, alvo_chars: int) -> str:
        llm_historiador = obter_llm(temperature=0.3)

        def pedir(limite: int, aviso: str = "") -> str:
            prompt = f"""Você é o Historiador de uma mesa de RPG cooperativo. Reduza o histórico de longo prazo do personagem {agente} abaixo.
            Preserve nomes, decisões, revelações e consequências importantes; descarte detalhes secundários e repetições.
            Escreva em prosa corrida, em terceira pessoa, sem tags e sem títulos.
            O limite máximo de caracteres para esse resumo é de {limite} caracteres.{aviso}

            HISTÓRICO:
            {mesa}"""
            return limpar_tags(texto_resposta(_invocar(llm_historiador, prompt)))

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

            # rodadas -> cena, sem disparar o ciclo automático do mesa
            GerenciadorMemoriaRPG.compilar_cenas(agente, encadear=False)

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
