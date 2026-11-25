"""
Testes dos adaptadores de IA, sem acesso à internet.

A função urlopen é substituída por uma falsa, que guarda a requisição enviada
e devolve uma resposta no formato de cada provedor. Assim é possível conferir
o que seria enviado e como a resposta é lida, sem consumir cota.
"""

import io
import json
import socket
import urllib.error
from datetime import date
from unittest import TestCase, mock

from integracao.ia.base import ErroNoServicoDeIA, PedidoDeRoteiro
from integracao.ia.gemini import ClienteGemini
from integracao.ia.groq import ClienteGroq
from integracao.ia.simulado import ClienteIASimulado

PEDIDO = PedidoDeRoteiro(
    destino="Paris, França",
    datas=[date(2026, 12, 1), date(2026, 12, 2)],
    estilo="Intenso",
    atividades_por_dia=6,
    preferencias=[("Gastronomia", 5), ("Cultura", 4)],
)
ROTEIRO = {"dias": [{"ordem": 1, "atividades": [{"nome": "Louvre", "hora_sugerida": "09:00"}]}]}


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def simular_urlopen(corpo_da_resposta):
    """Devolve (urlopen falso, lista onde as requisições ficam guardadas)."""
    enviadas = []

    def urlopen(requisicao, timeout):
        enviadas.append((requisicao, timeout))
        return RespostaFalsa(json.dumps(corpo_da_resposta).encode())

    return urlopen, enviadas


class TestesDoGroq(TestCase):
    def setUp(self):
        self.cliente = ClienteGroq("chave-de-teste", "openai/gpt-oss-120b", tempo_limite=15)

    def test_envia_prompt_modelo_e_chave_e_le_o_json_gerado(self):
        resposta = {"choices": [{"message": {"content": json.dumps(ROTEIRO)}}]}
        urlopen, enviadas = simular_urlopen(resposta)
        with mock.patch("urllib.request.urlopen", urlopen):
            self.assertEqual(self.cliente.sugerir_roteiro(PEDIDO), ROTEIRO)

        requisicao, tempo_limite = enviadas[0]
        corpo = json.loads(requisicao.data)
        self.assertEqual(requisicao.full_url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(requisicao.get_header("Authorization"), "Bearer chave-de-teste")
        self.assertEqual(corpo["model"], "openai/gpt-oss-120b")
        self.assertEqual(corpo["response_format"]["type"], "json_schema")
        self.assertIn("Paris, França", corpo["messages"][1]["content"])
        self.assertIn("Gastronomia (5/5)", corpo["messages"][1]["content"])
        self.assertEqual(tempo_limite, 15)

    def test_cota_esgotada_vira_erro_do_servico(self):
        def urlopen(requisicao, timeout):
            raise urllib.error.HTTPError(requisicao.full_url, 429, "Too Many Requests", {}, None)

        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaisesRegex(ErroNoServicoDeIA, "429"):
                self.cliente.sugerir_roteiro(PEDIDO)

    def test_tempo_esgotado_vira_erro_do_servico(self):
        with mock.patch("urllib.request.urlopen", side_effect=socket.timeout()):
            with self.assertRaises(ErroNoServicoDeIA):
                self.cliente.sugerir_roteiro(PEDIDO)

    def test_modelo_que_responde_texto_em_vez_de_json_vira_erro(self):
        urlopen, _ = simular_urlopen({"choices": [{"message": {"content": "Claro! Aqui está seu roteiro..."}}]})
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(ErroNoServicoDeIA):
                self.cliente.sugerir_roteiro(PEDIDO)

    def test_sem_chave_o_cliente_nem_e_criado(self):
        with self.assertRaisesRegex(ErroNoServicoDeIA, "GROQ_API_KEY"):
            ClienteGroq("", "openai/gpt-oss-120b", 15)


class TestesDoGemini(TestCase):
    def setUp(self):
        self.cliente = ClienteGemini("chave-de-teste", "gemini-3.8-flash", tempo_limite=15)

    def test_envia_a_chave_no_cabecalho_e_nunca_na_url(self):
        resposta = {"candidates": [{"content": {"parts": [{"text": json.dumps(ROTEIRO)}]}}]}
        urlopen, enviadas = simular_urlopen(resposta)
        with mock.patch("urllib.request.urlopen", urlopen):
            self.assertEqual(self.cliente.sugerir_roteiro(PEDIDO), ROTEIRO)

        requisicao, _ = enviadas[0]
        corpo = json.loads(requisicao.data)
        self.assertEqual(
            requisicao.full_url,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
        )
        self.assertNotIn("chave-de-teste", requisicao.full_url)
        self.assertEqual(requisicao.get_header("X-goog-api-key"), "chave-de-teste")
        self.assertEqual(corpo["generationConfig"]["responseMimeType"], "application/json")

    def test_resposta_dividida_em_partes_e_juntada(self):
        texto = json.dumps(ROTEIRO)
        resposta = {"candidates": [{"content": {"parts": [{"text": texto[:10]}, {"text": texto[10:]}]}}]}
        urlopen, _ = simular_urlopen(resposta)
        with mock.patch("urllib.request.urlopen", urlopen):
            self.assertEqual(self.cliente.sugerir_roteiro(PEDIDO), ROTEIRO)

    def test_resposta_bloqueada_sem_candidatos_vira_erro(self):
        urlopen, _ = simular_urlopen({"promptFeedback": {"blockReason": "OTHER"}})
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(ErroNoServicoDeIA):
                self.cliente.sugerir_roteiro(PEDIDO)


class TestesDoPrompt(TestCase):
    def test_categorias_do_prompt_sao_as_mesmas_do_dominio(self):
        from dominio.regras import CATEGORIAS as DO_DOMINIO
        from integracao.ia.prompt import CATEGORIAS as DO_PROMPT

        self.assertEqual(DO_PROMPT, DO_DOMINIO)

    def test_instrucoes_pedem_a_categoria(self):
        from integracao.ia.prompt import INSTRUCOES_DO_SISTEMA

        self.assertIn("Cultura, Gastronomia, Arte, Natureza, História, Compras, Vida noturna, Praia", INSTRUCOES_DO_SISTEMA)
        self.assertIn('"categoria": "Cultura"', INSTRUCOES_DO_SISTEMA)


class TestesDoSimulado(TestCase):
    def test_destino_conhecido_usa_locais_com_coordenadas(self):
        roteiro = ClienteIASimulado().sugerir_roteiro(PEDIDO)
        primeira = roteiro["dias"][0]["atividades"][0]
        self.assertIsNotNone(primeira["latitude"])
        self.assertTrue(all(a["categoria"] for dia in roteiro["dias"] for a in dia["atividades"]))

    def test_destino_ignora_acento_e_pais(self):
        pedido = PedidoDeRoteiro("toquio", [date(2026, 12, 1)], None, 4)
        nomes = [a["nome"] for a in ClienteIASimulado().sugerir_roteiro(pedido)["dias"][0]["atividades"]]
        self.assertIn("Templo Sensō-ji", nomes)

    def test_destino_desconhecido_recebe_sugestoes_genericas(self):
        pedido = PedidoDeRoteiro("Brasília, Brasil", [date(2026, 12, 1)], None, 3)
        atividades = ClienteIASimulado().sugerir_roteiro(pedido)["dias"][0]["atividades"]
        self.assertEqual(atividades[0]["nome"], "Centro histórico de Brasília")
        self.assertEqual(len(atividades), 3)
