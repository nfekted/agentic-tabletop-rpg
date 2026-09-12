# Ponto de entrada do sistema RPG Agent em modo TERMINAL (menu de texto).
# Para a versão visual, rode: streamlit run app.py

from config import AGENTES
from fichas import obter_status_jogador
from imagens import selecionar_imagem_interativa
from memoria import obter_pasta_agente, GerenciadorMemoriaRPG
from agentes import gerar_resposta_agente


def main():
    print("==================================================")
    print("            INICIANDO SISTEMA RPG AGENT           ")
    print("==================================================")

    # Garante que as pastas de memória existem
    for ag in AGENTES:
        obter_pasta_agente(ag)

    historico_em_memoria = []
    rodada_ativa = False
    envolvidos_rodada_atual = set()

    while True:
        print("\n--- MENU DO MESTRE ---")
        print("1. [Inicio da rodada]")
        print("2. [Fim da rodada]")
        print("3. Falar com Todos (Público)")
        print("4. Falar com Jogador(es) Específico(s) [Cena Pública]")
        print("5. Cena Privada (Apenas para Jogador(es) Selecionado(s))")
        print("6. Sair")

        opcao = input("Escolha uma opção (1-6): ").strip()

        if opcao == "6":
            break

        if opcao == "1":
            rodada_ativa = True
            envolvidos_rodada_atual = set()
            msg = "--- ÍNICIO DA RODADA ---"
            print(f"\n🟢 {msg}")
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(msg, AGENTES)
            continue

        if opcao == "2":
            if not rodada_ativa:
                print("⚠️ Inicie a rodada antes de finalizar.")
                continue

            msg = "--- FIM DA RODADA ---"
            alvos_finalizacao = (
                list(envolvidos_rodada_atual) if envolvidos_rodada_atual else AGENTES
            )
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(msg, alvos_finalizacao)
            GerenciadorMemoriaRPG.finalizar_rodada(alvos_finalizacao)

            nao_envolvidos = [ag for ag in AGENTES if ag not in alvos_finalizacao]
            if nao_envolvidos:
                GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

            rodada_ativa = False
            historico_em_memoria = []
            continue

        presentes = []
        is_privado = False

        if opcao == "3":
            presentes = AGENTES.copy()
        elif opcao in ["4", "5"]:
            is_privado = opcao == "5"
            print(f"\nJogadores disponíveis: {', '.join(AGENTES)}")
            entrada = input(
                "Digite o(s) jogador(es) envolvidos separados por vírgula: "
            ).strip()

            presentes = [p.strip() for p in entrada.split(",") if p.strip() in AGENTES]

            if not presentes:
                print("⚠️ Nenhum jogador válido selecionado!")
                continue
        else:
            print("Opção inválida!")
            continue

        agentes_alvo_log = presentes if is_privado else AGENTES
        for p in agentes_alvo_log:
            envolvidos_rodada_atual.add(p)

        tipo_cena_label = "[PRIVADO]" if is_privado else "[PÚBLICO]"
        comando_mestre = input(
            f"Sua descrição/orientação para '{', '.join(presentes)}' {tipo_cena_label}: "
        ).strip()

        anexar = input("Deseja anexar uma imagem? (s/n): ").strip().lower()
        img_selecionada = None

        if anexar == "s":
            img_selecionada = selecionar_imagem_interativa(pasta_base="img")

        log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
        historico_em_memoria.append(log_mestre)

        if rodada_ativa:
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)

        if opcao == "3":
            print("\n--- Reações dos Jogadores ---")
            for ag in presentes:
                status = obter_status_jogador(ag)
                if status != "vivo":
                    continue

                resposta = gerar_resposta_agente(
                    ag,
                    f"O mestre disse a todos: '{comando_mestre}'. Dê sua reação breve.",
                    historico_em_memoria,
                    caminho_imagem=img_selecionada,
                )
                print(f"💬 {ag}: {resposta}")
                log_ag = f"{ag}: {resposta}"
                historico_em_memoria.append(log_ag)
                if rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_ag, AGENTES)

        else:
            alvo_principal = presentes[0]

            status_alvo = obter_status_jogador(alvo_principal)
            if status_alvo != "vivo":
                print(
                    f"\n⚠️ Não é possível falar com {alvo_principal}. O personagem está: [{status_alvo.upper()}]."
                )
                continue

            resposta_agente = gerar_resposta_agente(
                alvo_principal,
                f"O mestre direcionou a você: '{comando_mestre}'. Responda usando [acao] para agir ou [duvida] para consultar outro jogador.",
                historico_em_memoria,
                caminho_imagem=img_selecionada,
            )

            print(f"\n🤖 Retorno de {alvo_principal}:")
            print(f"👉 {resposta_agente}")

            confirmar = (
                input("\n[Mestre] Deseja espelhar/aprovar essa mensagem? (s/n): ")
                .strip()
                .lower()
            )

            if confirmar == "s":
                log_acao = f"{alvo_principal}: {resposta_agente}"
                historico_em_memoria.append(log_acao)
                if rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_log_rodada_atual(
                        log_acao, agentes_alvo_log
                    )

                outros_presentes = [p for p in presentes if p != alvo_principal]
                tem_duvida = "[duvida]" in resposta_agente.lower()
                tem_acao = "[acao]" in resposta_agente.lower()

                if tem_duvida and outros_presentes:
                    candidatos = [
                        p for p in outros_presentes if obter_status_jogador(p) == "vivo"
                    ]

                    if not candidatos:
                        print(
                            "\n⚠️ Há uma dúvida na resposta, mas nenhum outro jogador presente está disponível para respondê-la."
                        )
                    else:
                        print(
                            f"\n❓ {alvo_principal} fez uma pergunta/dúvida na resposta."
                        )
                        print(
                            f"Jogadores presentes disponíveis: {', '.join(candidatos)}"
                        )
                        destino_input = input(
                            "[Mestre] Para quem deseja redirecionar essa dúvida? "
                            "(nome, vários separados por vírgula, ou Enter para não redirecionar): "
                        ).strip()

                        destinos = [
                            d.strip()
                            for d in destino_input.split(",")
                            if d.strip() in candidatos
                        ]

                        if not destinos:
                            print(
                                "↪️ Nenhum redirecionamento autorizado. A dúvida fica sem resposta direta por ora."
                            )
                        else:
                            for destino in destinos:
                                resp_redirecionada = gerar_resposta_agente(
                                    destino,
                                    f"{alvo_principal} perguntou diretamente a você: '{resposta_agente}'. "
                                    f"Responda a pergunta dele(a) diretamente, sem apenas opinar sobre o assunto.",
                                    historico_em_memoria,
                                    caminho_imagem=None,
                                )
                                print(
                                    f"\n🤖 Retorno de {destino} (resposta à pergunta de {alvo_principal}):"
                                )
                                print(f"👉 {resp_redirecionada}")

                                confirmar_redirect = (
                                    input(
                                        f"[Mestre] Deseja espelhar/aprovar a resposta de {destino}? (s/n): "
                                    )
                                    .strip()
                                    .lower()
                                )

                                if confirmar_redirect == "s":
                                    log_redirect = f"{destino} (resposta a {alvo_principal}): {resp_redirecionada}"
                                    historico_em_memoria.append(log_redirect)
                                    if rodada_ativa:
                                        GerenciadorMemoriaRPG.salvar_log_rodada_atual(
                                            log_redirect, agentes_alvo_log
                                        )
                                else:
                                    print(
                                        f"❌ Resposta de {destino} descartada pelo Mestre. Nenhuma alteração foi salva na história."
                                    )

                elif tem_acao:
                    print(
                        f"✅ Ação de {alvo_principal} resolvida. Nenhuma reação automática dos demais."
                    )

                elif outros_presentes:
                    print(
                        f"\n--- Espelhando mensagem para os presentes na cena ({', '.join(outros_presentes)}) ---"
                    )

                    for ou in outros_presentes:
                        if obter_status_jogador(ou) != "vivo":
                            continue

                        resp_outro = gerar_resposta_agente(
                            ou,
                            f"O jogador {alvo_principal} acabou de dizer/fazer: '{resposta_agente}'. Você concorda, opina ou faz ressalva? Seja breve.",
                            historico_em_memoria,
                            caminho_imagem=None,
                        )
                        print(f"💬 {ou}: {resp_outro}")
                        log_outro = f"{ou} (opinião): {resp_outro}"
                        historico_em_memoria.append(log_outro)
                        if rodada_ativa:
                            GerenciadorMemoriaRPG.salvar_log_rodada_atual(
                                log_outro, agentes_alvo_log
                            )
            else:
                print(
                    "❌ Mensagem descartada pelo Mestre. Nenhuma alteração foi salva na história."
                )


if __name__ == "__main__":
    main()
