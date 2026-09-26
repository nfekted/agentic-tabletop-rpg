import os
import unittest
from turno import (
    iniciar_turno,
    encerrar_turno,
    carregar_turno,
    turno_ativo,
    adicionar_area,
    remover_area,
    vincular_participante,
    desvincular_participante,
    adicionar_token_ao_turno,
    remover_token_do_turno,
    atualizar_ficha_token,
    atualizar_ordem_participante,
    verificar_empates,
    avancar_proxima_acao,
)


class TestModoTurnos(unittest.TestCase):
    def setUp(self):
        encerrar_turno()

    def tearDown(self):
        encerrar_turno()

    def test_ciclo_vida_basico(self):
        self.assertFalse(turno_ativo())
        agentes = ["Aniela", "Leandro"]
        dados = iniciar_turno(agentes)
        self.assertTrue(turno_ativo())
        self.assertFalse(dados["em_andamento"])
        self.assertIsNone(dados["ordem_atual"])
        self.assertEqual(len(dados["personagens"]), 2)
        self.assertEqual(dados["personagens"][0]["nome"], "Aniela")
        self.assertEqual(dados["personagens"][0]["id"], "p_Aniela")

        encerrar_turno()
        self.assertFalse(turno_ativo())

    def test_gestao_areas(self):
        iniciar_turno(["Aniela"])
        area_id = adicionar_area("Entrada da Masmorra")
        self.assertIsNotNone(area_id)
        dados = carregar_turno()
        self.assertEqual(len(dados["areas"]), 1)
        self.assertEqual(dados["areas"][0]["nome"], "Entrada da Masmorra")

        # Vincular
        ok = vincular_participante(area_id, "p_Aniela")
        self.assertTrue(ok)
        dados = carregar_turno()
        self.assertIn("p_Aniela", dados["areas"][0]["participantes"])

        # Desvincular
        ok_desv = desvincular_participante("p_Aniela")
        self.assertTrue(ok_desv)
        dados = carregar_turno()
        self.assertNotIn("p_Aniela", dados["areas"][0]["participantes"])

        # Remover area
        remover_area(area_id)
        dados = carregar_turno()
        self.assertEqual(len(dados["areas"]), 0)

    def test_tokens_e_duplicatas(self):
        iniciar_turno(["Leandro"])
        tok1 = adicionar_token_ao_turno("inimigo", "default.txt")
        self.assertIsNotNone(tok1)
        self.assertEqual(tok1["nome_exibicao"], "Default 1")
        self.assertEqual(tok1["tipo_icone"], "⚔️")

        tok2 = adicionar_token_ao_turno("inimigo", "default.txt")
        self.assertEqual(tok2["nome_exibicao"], "Default 2")

        # Atualizar ficha
        nova_ficha = {"conteudo": "Esqueleto modificado", "status": [{"nome": "Vida", "valor_atual": 8, "valor_max": 10, "cor": "#DC143C"}]}
        atualizar_ficha_token(tok1["id"], nova_ficha)
        dados = carregar_turno()
        t1 = [t for t in dados["tokens"] if t["id"] == tok1["id"]][0]
        self.assertEqual(t1["ficha_dados"]["conteudo"], "Esqueleto modificado")

        # Remover token
        remover_token_do_turno(tok1["id"])
        dados = carregar_turno()
        self.assertEqual(len(dados["tokens"]), 1)
        self.assertEqual(dados["tokens"][0]["id"], tok2["id"])

    def test_ordem_empate_e_fluxo(self):
        iniciar_turno(["Aniela", "Leandro"])
        tok = adicionar_token_ao_turno("inimigo", "default.txt")

        # Define ordens
        atualizar_ordem_participante("p_Aniela", 1)
        atualizar_ordem_participante("p_Leandro", 2)
        atualizar_ordem_participante(tok["id"], 2)  # Empate com Leandro!

        dados = carregar_turno()
        empates = verificar_empates(dados)
        self.assertEqual(empates, [2])

        # Tentar avançar com empate deve falhar
        ok, msg = avancar_proxima_acao(dados)
        self.assertFalse(ok)
        self.assertIn("Empate detectado", msg)

        # Corrige empate
        atualizar_ordem_participante(tok["id"], 5)
        dados = carregar_turno()
        self.assertEqual(verificar_empates(dados), [])

        # Inicia combate: deve ir para ordem 1 (Aniela)
        ok, msg = avancar_proxima_acao(dados)
        self.assertTrue(ok)
        dados = carregar_turno()
        self.assertTrue(dados["em_andamento"])
        self.assertEqual(dados["ordem_atual"], 1)

        # Próxima ação: deve ir para ordem 2 (Leandro)
        ok, msg = avancar_proxima_acao(dados)
        self.assertTrue(ok)
        dados = carregar_turno()
        self.assertEqual(dados["ordem_atual"], 2)

        # Próxima ação: deve ir para ordem 5 (Token)
        ok, msg = avancar_proxima_acao(dados)
        self.assertTrue(ok)
        dados = carregar_turno()
        self.assertEqual(dados["ordem_atual"], 5)

        # Próxima ação: fim da rodada -> deve reiniciar para ordem 1 (Nova Rodada)
        ok, msg = avancar_proxima_acao(dados)
        self.assertTrue(ok)
        self.assertIn("Nova Rodada", msg)
        dados = carregar_turno()
        self.assertEqual(dados["ordem_atual"], 1)


if __name__ == "__main__":
    unittest.main()
