# Ponto de entrada do sistema RPG Agent em modo TERMINAL (menu de texto).
# Para a versão visual, rode: streamlit run app.py

import os
from config import carregar_agentes
from imagens import selecionar_imagem_interativa
from memoria import obter_pasta_agente, GerenciadorMemoriaRPG
from agentes import gerar_resposta_agente
from tags import (
    extrair_tags_resposta,
    formatar_conteudo_publico,
    tem_acao,
    tem_duvida,
    apenas_pensamento,
)


def main():
    print("==================================================")
    print("            INICIANDO SISTEMA RPG AGENT           ")
    print("==================================================")

    # Garante que as pastas de memória existem
    for ag in carregar_agentes():
        obter_pasta_agente(ag)

    historico_em_memoria = []
    rodada_ativa = False
    envolvidos_rodada_atual = set()

    while True:
        agentes = carregar_agentes()

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
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(msg, agentes)
            continue

        if opcao == "2":
            if not rodada_ativa:
                print("⚠️ Inicie a rodada antes de finalizar.")
                continue

            msg = "--- FIM DA RODADA ---"
            alvos_finalizacao = (
                list(envolvidos_rodada_atual) if envolvidos_rodada_atual else agentes
            )
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(msg, alvos_finalizacao)
            GerenciadorMemoriaRPG.finalizar_rodada(alvos_finalizacao)

            nao_envolvidos = [ag for ag in agentes if ag not in alvos_finalizacao]
            if nao_envolvidos:
                GerenciadorMemoriaRPG.limpar_temp_nao_envolvidos(nao_envolvidos)

            rodada_ativa = False
            historico_em_memoria = []
            continue

        presentes = []
        is_privado = False

        if opcao == "3":
            presentes = agentes.copy()
        elif opcao in ["4", "5"]:
            is_privado = opcao == "5"
            print(f"\nJogadores disponíveis: {', '.join(agentes)}")
            entrada = input(
                "Digite o(s) jogador(es) envolvidos separados por vírgula: "
            ).strip()

            presentes = [p.strip() for p in entrada.split(",") if p.strip() in agentes]

            if not presentes:
                print("⚠️ Nenhum jogador válido selecionado!")
                continue
        else:
            print("Opção inválida!")
            continue

        agentes_alvo_log = presentes if is_privado else agentes
        for p in agentes_alvo_log:
            envolvidos_rodada_atual.add(p)

        tipo_cena_label = "[PRIVADO]" if is_privado else "[PÚBLICO]"
        comando_mestre = input(
            f"Sua descrição/orientação para '{', '.join(presentes)}' {tipo_cena_label}: "
        ).strip()

        anexar = input("Deseja anexar uma imagem? (s/n): ").strip().lower()
        img_selecionada = None

        if anexar == "s":
            img_selecionada = selecionar_imagem_interativa(
                pasta_base=os.path.join("arquivos", "img")
            )

        log_mestre = f"Mestre (para {', '.join(presentes)}): {comando_mestre}"
        historico_em_memoria.append(log_mestre)

        if rodada_ativa:
            GerenciadorMemoriaRPG.salvar_log_rodada_atual(log_mestre, agentes_alvo_log)

        if opcao == "3":
            print("\n--- Reações dos Jogadores ---")
            for ag in presentes:
                resposta = gerar_resposta_agente(
                    ag,
                    f"O mestre disse a todos: '{comando_mestre}'. Dê sua reação no formato com tags [pensamento], [fala], [acao] ou [duvida].",
                    historico_em_memoria,
                    caminho_imagem=img_selecionada,
                )
                tags = extrair_tags_resposta(resposta)
                publico = formatar_conteudo_publico(tags)

                if tags.get("pensamento"):
                    print(f"💭 [{ag} (pensamento)]: {tags['pensamento']}")
                if publico:
                    print(f"💬 {ag}: {publico}")
                    log_ag = f"{ag}: {publico}"
                    historico_em_memoria.append(log_ag)
                    if rodada_ativa:
                        GerenciadorMemoriaRPG.salvar_resposta_agente(
                            ag, resposta, presentes
                        )
                elif tags.get("pensamento") and rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(ag, resposta, [ag])

        else:
            alvo_principal = presentes[0]

            resposta_agente = gerar_resposta_agente(
                alvo_principal,
                f"O mestre direcionou a você: '{comando_mestre}'. Responda usando as tags [pensamento], [fala], [acao] ou [duvida].",
                historico_em_memoria,
                caminho_imagem=img_selecionada,
            )

            tags = extrair_tags_resposta(resposta_agente)
            publico = formatar_conteudo_publico(tags)

            print(f"\n🤖 Retorno de {alvo_principal}:")
            if tags.get("pensamento"):
                print(f"💭 [Pensamento Íntimo]: {tags['pensamento']}")
            if tags.get("fala"):
                print(f"🗣️ [Fala]: \"{tags['fala']}\"")
            if tags.get("acao"):
                print(f"⚔️ [Ação]: {tags['acao']}")
            if tags.get("duvida"):
                print(f"❓ [Dúvida]: {tags['duvida']}")
            if not (tags.get("fala") or tags.get("acao") or tags.get("duvida")):
                print(f"👉 {resposta_agente}")

            if apenas_pensamento(tags):
                print(
                    f"\n💭 {alvo_principal} teve apenas um pensamento privado. Nenhuma ação pública a aprovar."
                )
                if rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(
                        alvo_principal, resposta_agente, [alvo_principal]
                    )
                continue

            confirmar = (
                input(
                    "\n[Mestre] Deseja espelhar/aprovar essa fala/ação pública? (s/n): "
                )
                .strip()
                .lower()
            )

            if confirmar == "s":
                conteudo_salvar = publico or resposta_agente
                log_acao = f"{alvo_principal}: {conteudo_salvar}"
                historico_em_memoria.append(log_acao)
                if rodada_ativa:
                    GerenciadorMemoriaRPG.salvar_resposta_agente(
                        alvo_principal, resposta_agente, agentes_alvo_log
                    )

                outros_presentes = [p for p in presentes if p != alvo_principal]

                if tem_duvida(tags) and outros_presentes:
                    candidatos = list(outros_presentes)

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
                                    f"{alvo_principal} perguntou diretamente a você: '{tags.get('duvida') or publico}'. "
                                    f"Responda diretamente usando as tags [pensamento], [fala], [acao] ou [duvida].",
                                    historico_em_memoria,
                                    caminho_imagem=None,
                                )
                                tags_red = extrair_tags_resposta(resp_redirecionada)
                                pub_red = formatar_conteudo_publico(tags_red)

                                print(
                                    f"\n🤖 Retorno de {destino} (resposta à pergunta de {alvo_principal}):"
                                )
                                if tags_red.get("pensamento"):
                                    print(
                                        f"💭 [Pensamento Íntimo]: {tags_red['pensamento']}"
                                    )
                                if tags_red.get("fala"):
                                    print(f"🗣️ [Fala]: \"{tags_red['fala']}\"")
                                if tags_red.get("acao"):
                                    print(f"⚔️ [Ação]: {tags_red['acao']}")
                                if tags_red.get("duvida"):
                                    print(f"❓ [Dúvida]: {tags_red['duvida']}")
                                if not (
                                    tags_red.get("fala")
                                    or tags_red.get("acao")
                                    or tags_red.get("duvida")
                                ):
                                    print(f"👉 {resp_redirecionada}")

                                if apenas_pensamento(tags_red):
                                    if rodada_ativa:
                                        GerenciadorMemoriaRPG.salvar_resposta_agente(
                                            destino, resp_redirecionada, [destino]
                                        )
                                    continue

                                confirmar_redirect = (
                                    input(
                                        f"[Mestre] Deseja espelhar/aprovar a resposta de {destino}? (s/n): "
                                    )
                                    .strip()
                                    .lower()
                                )

                                if confirmar_redirect == "s":
                                    conteudo_red_salvar = pub_red or resp_redirecionada
                                    log_redirect = f"{destino} (resposta a {alvo_principal}): {conteudo_red_salvar}"
                                    historico_em_memoria.append(log_redirect)
                                    if rodada_ativa:
                                        GerenciadorMemoriaRPG.salvar_resposta_agente(
                                            destino,
                                            resp_redirecionada,
                                            agentes_alvo_log,
                                        )
                                else:
                                    print(
                                        f"❌ Resposta de {destino} descartada pelo Mestre. Nenhuma alteração foi salva na história."
                                    )

                elif tem_acao(tags):
                    print(
                        f"✅ Ação de {alvo_principal} resolvida. Nenhuma reação automática dos demais."
                    )

                elif outros_presentes:
                    print(
                        f"\n--- Espelhando mensagem para os presentes na cena ({', '.join(outros_presentes)}) ---"
                    )

                    for ou in outros_presentes:
                        resp_outro = gerar_resposta_agente(
                            ou,
                            f"O jogador {alvo_principal} acabou de dizer/fazer: '{publico}'. Você concorda, opina ou faz ressalva? Use as tags [pensamento], [fala], [acao] ou [duvida]. Seja breve.",
                            historico_em_memoria,
                            caminho_imagem=None,
                        )
                        tags_ou = extrair_tags_resposta(resp_outro)
                        pub_ou = formatar_conteudo_publico(tags_ou)

                        if tags_ou.get("pensamento"):
                            print(f"💭 [{ou} (pensamento)]: {tags_ou['pensamento']}")
                        if pub_ou:
                            print(f"💬 {ou}: {pub_ou}")
                            log_outro = f"{ou} (opinião): {pub_ou}"
                            historico_em_memoria.append(log_outro)
                            if rodada_ativa:
                                GerenciadorMemoriaRPG.salvar_resposta_agente(
                                    ou, resp_outro, agentes_alvo_log
                                )
                        elif tags_ou.get("pensamento") and rodada_ativa:
                            GerenciadorMemoriaRPG.salvar_resposta_agente(
                                ou, resp_outro, [ou]
                            )
            else:
                print(
                    "❌ Mensagem descartada pelo Mestre. Nenhuma alteração foi salva na história."
                )


if __name__ == "__main__":
    main()
