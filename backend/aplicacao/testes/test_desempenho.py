"""
Verificação do RQ009 (desempenho).

    O sistema deverá responder às consultas e às operações de edição do
    roteiro em menos de 1 segundo e apresentar o roteiro gerado
    automaticamente em até 15 segundos após o envio das preferências,
    considerando o tempo de resposta do serviço externo de IA.

Os testes usam a maior viagem permitida (30 dias) com o maior número de
atividades por dia (6, ritmo Intenso): 180 atividades. Se o pior caso fica
abaixo do limite, os casos menores também ficam.

O tempo de geração com um provedor real depende da rede e do provedor, e não
pode ser medido aqui sem consumir cota. O que se verifica é o que está sob
controle do sistema: o limite de espera configurado e o tempo do restante do
processamento, medido com o cliente simulado.
"""

import time
from datetime import date, timedelta

from django.conf import settings
from django.test import override_settings

from dominio.regras import DURACAO_MAXIMA_EM_DIAS

from .test_api import BaseDeTeste

LIMITE_CONSULTA_E_EDICAO = 1.0   # segundos
LIMITE_GERACAO = 15.0            # segundos


@override_settings(IA_PROVEDOR="simulado")
class TestesDeDesempenho(BaseDeTeste):
    def setUp(self):
        super().setUp()
        inicio = date.today() + timedelta(days=30)
        self.viagem = self.criar_viagem(dias=DURACAO_MAXIMA_EM_DIAS, inicio=inicio, estilo_viagem="Intenso").data
        # Preenche os 30 dias com 6 atividades cada, à mão.
        for dia in self.viagem["dias"]:
            for posicao in range(6):
                self.client.post(
                    f"/api/dias/{dia['id_dia']}/atividades/",
                    {"local": {"nome": f"Local {dia['ordem']}-{posicao}", "latitude": 38.7, "longitude": -9.1}},
                    format="json",
                )

    def medir(self, requisicao):
        inicio = time.perf_counter()
        resposta = requisicao()
        return resposta, time.perf_counter() - inicio

    def test_consulta_do_roteiro_completo_em_menos_de_1_segundo(self):
        resposta, segundos = self.medir(lambda: self.client.get(f"/api/viagens/{self.viagem['id_viagem']}/"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(sum(len(d["atividades"]) for d in resposta.data["dias"]), 180)
        self.assertLess(segundos, LIMITE_CONSULTA_E_EDICAO)

    def test_reordenacao_em_menos_de_1_segundo(self):
        dia = self.client.get(f"/api/viagens/{self.viagem['id_viagem']}/").data["dias"][0]
        nova_ordem = [a["id_atividade"] for a in reversed(dia["atividades"])]
        resposta, segundos = self.medir(
            lambda: self.client.post(f"/api/dias/{dia['id_dia']}/reordenar/", {"ordem": nova_ordem}, format="json")
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertLess(segundos, LIMITE_CONSULTA_E_EDICAO)

    def test_processamento_da_geracao_cabe_na_folga_do_limite(self):
        """O que sobra dos 15 segundos depois da espera máxima pelo provedor."""
        folga = LIMITE_GERACAO - settings.IA_TEMPO_LIMITE
        self.assertGreater(folga, 0, "a espera pelo provedor não pode consumir todo o limite do RQ009")

        resposta, segundos = self.medir(
            lambda: self.client.post(
                f"/api/viagens/{self.viagem['id_viagem']}/gerar-roteiro/", {"substituir": True}, format="json"
            )
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertLess(segundos, folga)
