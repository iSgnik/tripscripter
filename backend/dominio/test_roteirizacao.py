"""Testes da validação da sugestão da IA. Não usam banco nem internet."""

from datetime import time
from decimal import Decimal
from unittest import TestCase

from dominio.roteirizacao import RespostaDeIAInvalida, atividades_por_dia, validar_sugestao


def atividade(nome, **campos):
    return {"nome": nome, "hora_sugerida": "10:00", **campos}


class TestesDaValidacao(TestCase):
    def test_sugestao_correta_e_aproveitada_inteira(self):
        sugestao = {
            "dias": [
                {"ordem": 1, "atividades": [atividade("Louvre", latitude=48.86, longitude=2.33, custo_estimado=22)]},
                {"ordem": 2, "atividades": [atividade("Orsay")]},
            ]
        }
        dias = validar_sugestao(sugestao, total_de_dias=2, maximo_por_dia=4)
        self.assertEqual(dias[0][0]["latitude"], Decimal("48.860000"))
        self.assertEqual(dias[0][0]["custo_estimado"], Decimal("22.00"))
        self.assertEqual(dias[1][0]["nome"], "Orsay")

    def test_coordenada_fora_do_planeta_e_descartada_mas_a_atividade_fica(self):
        dias = validar_sugestao({"dias": [{"ordem": 1, "atividades": [atividade("X", latitude=200, longitude=2)]}]}, 1, 4)
        self.assertEqual(dias[0][0]["nome"], "X")
        self.assertIsNone(dias[0][0]["latitude"])
        self.assertIsNone(dias[0][0]["longitude"])

    def test_coordenada_zero_zero_e_tratada_como_desconhecida(self):
        dias = validar_sugestao({"dias": [{"ordem": 1, "atividades": [atividade("X", latitude=0, longitude=0)]}]}, 1, 4)
        self.assertIsNone(dias[0][0]["latitude"])

    def test_custo_negativo_ou_texto_vira_nulo(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [atividade("A", custo_estimado=-5), atividade("B", custo_estimado="caro")]}]}
        dias = validar_sugestao(sugestao, 1, 4)
        self.assertEqual([a["custo_estimado"] for a in dias[0]], [None, None])

    def test_hora_aceita_formato_brasileiro_e_recusa_hora_invalida(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [atividade("A", hora_sugerida="9h30"), atividade("B", hora_sugerida="25:00")]}]}
        dias = validar_sugestao(sugestao, 1, 4)
        self.assertEqual(dias[0][0]["hora_sugerida"], time(9, 30))
        self.assertIsNone(dias[0][1]["hora_sugerida"])

    def test_atividades_ficam_em_ordem_cronologica_e_sem_horario_vai_para_o_fim(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [
            atividade("Jantar", hora_sugerida="20:00"), atividade("Sem hora", hora_sugerida=None), atividade("Café", hora_sugerida="08:00"),
        ]}]}
        self.assertEqual([a["nome"] for a in validar_sugestao(sugestao, 1, 4)[0]], ["Café", "Jantar", "Sem hora"])

    def test_lugar_repetido_em_outro_dia_e_descartado(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [atividade("Louvre")]}, {"ordem": 2, "atividades": [atividade("louvre")]}]}
        self.assertEqual(validar_sugestao(sugestao, 2, 4)[1], [])

    def test_excesso_de_atividades_e_cortado_no_limite_do_ritmo(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [atividade(f"Lugar {i}") for i in range(10)]}]}
        self.assertEqual(len(validar_sugestao(sugestao, 1, maximo_por_dia=3)[0]), 3)

    def test_dia_alem_do_periodo_e_ignorado(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [atividade("A")]}, {"ordem": 5, "atividades": [atividade("B")]}]}
        self.assertEqual(len(validar_sugestao(sugestao, 2, 4)), 2)

    def test_texto_longo_e_cortado_no_tamanho_da_coluna(self):
        dias = validar_sugestao({"dias": [{"ordem": 1, "atividades": [atividade("N" * 500)]}]}, 1, 4)
        self.assertEqual(len(dias[0][0]["nome"]), 150)

    def test_sugestao_sem_nada_aproveitavel_e_recusada(self):
        for invalida in ({}, {"dias": "texto"}, {"dias": [{"ordem": 1, "atividades": [{"nome": ""}, 42]}]}):
            with self.assertRaises(RespostaDeIAInvalida):
                validar_sugestao(invalida, 1, 4)

    def test_categoria_aceita_variacao_de_escrita_e_recusa_valor_fora_da_lista(self):
        sugestao = {"dias": [{"ordem": 1, "atividades": [
            atividade("A", categoria="cultura"),
            atividade("B", categoria="Vida  Noturna"),
            atividade("C", categoria="Esportes"),
            atividade("D"),
        ]}]}
        categorias = [a["categoria"] for a in validar_sugestao(sugestao, 1, 4)[0]]
        self.assertEqual(categorias, ["Cultura", "Vida noturna", None, None])

    def test_ritmo_define_atividades_por_dia(self):
        self.assertLess(atividades_por_dia("Tranquilo"), atividades_por_dia("Intenso"))
        self.assertEqual(atividades_por_dia(None), 4)
