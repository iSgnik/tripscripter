"""Testes das regras de domínio, que não dependem de banco de dados."""

from datetime import date
from unittest import TestCase

from comum.excecoes import RegraDeNegocioViolada
from dominio import regras


class TestesDeRegras(TestCase):
    def test_datas_da_viagem_incluem_o_primeiro_e_o_ultimo_dia(self):
        datas = regras.datas_da_viagem(date(2026, 12, 30), date(2027, 1, 2))
        self.assertEqual(datas, [date(2026, 12, 30), date(2026, 12, 31), date(2027, 1, 1), date(2027, 1, 2)])

    def test_viagem_de_um_dia_e_valida(self):
        regras.validar_periodo(date(2026, 12, 1), date(2026, 12, 1))

    def test_limite_de_duracao(self):
        regras.validar_periodo(date(2026, 12, 1), date(2026, 12, 30))  # 30 dias: aceito
        with self.assertRaises(RegraDeNegocioViolada):
            regras.validar_periodo(date(2026, 12, 1), date(2026, 12, 31))  # 31 dias

    def test_nova_ordem_nao_pode_duplicar_atividade(self):
        with self.assertRaises(RegraDeNegocioViolada):
            regras.validar_nova_ordem([1, 2, 3], [1, 1, 2])
