"""
Testes da geração de roteiro pela API (RQ004).

Usam o cliente simulado ou clientes falsos definidos aqui: nenhum teste chama
a internet nem consome cota de provedor.
"""

from django.test import override_settings

from integracao.ia import ClienteIA, ErroNoServicoDeIA
from persistencia.models import AtividadeRoteiro, Local

from .test_api import BaseDeTeste


class ClienteQueFalha(ClienteIA):
    nome = "Falho"

    def sugerir_roteiro(self, pedido):
        raise ErroNoServicoDeIA("simulação de falha")


@override_settings(IA_PROVEDOR="simulado", IA_RESERVA="simulado")
class TestesDeGeracao(BaseDeTeste):
    def setUp(self):
        super().setUp()
        self.client.put(
            "/api/preferencias/", {"preferencias": [{"categoria": "Cultura", "nivel_interesse": 5}]}, format="json"
        )

    def nova_viagem(self, destino="Paris, França", dias=3, estilo="Equilibrado"):
        return self.criar_viagem(dias=dias, destino=destino, estilo_viagem=estilo).data

    def gerar(self, viagem, **corpo):
        return self.client.post(f"/api/viagens/{viagem['id_viagem']}/gerar-roteiro/", corpo, format="json")

    def test_geracao_preenche_os_dias_e_informa_provedor_e_tempo(self):
        resposta = self.gerar(self.nova_viagem())
        self.assertEqual(resposta.status_code, 200, resposta.data)
        geracao, viagem = resposta.data["geracao"], resposta.data["viagem"]
        self.assertEqual(geracao["provedor"], "Simulado")
        self.assertIsNone(geracao["aviso"])
        self.assertGreaterEqual(geracao["tempo_em_ms"], 0)
        self.assertTrue(all(len(dia["atividades"]) == 4 for dia in viagem["dias"][:2]))

    def test_locais_gerados_tem_coordenadas_para_o_mapa(self):
        viagem = self.gerar(self.nova_viagem()).data["viagem"]
        self.assertIsNotNone(viagem["dias"][0]["atividades"][0]["local"]["latitude"])

    def test_locais_gerados_tem_categoria(self):
        viagem = self.gerar(self.nova_viagem()).data["viagem"]
        categorias = {a["local"]["categoria"] for dia in viagem["dias"] for a in dia["atividades"]}
        self.assertTrue(categorias)
        self.assertNotIn(None, categorias)

    def test_local_antigo_sem_categoria_e_completado_pela_geracao(self):
        Local.objects.create(nome="Museu do Louvre", latitude=48.8606, longitude=2.3376)
        self.gerar(self.nova_viagem())
        self.assertEqual(Local.objects.get(nome="Museu do Louvre").categoria, "Arte")

    def test_categoria_ja_gravada_nao_e_trocada_pela_ia(self):
        Local.objects.create(nome="Museu do Louvre", latitude=48.8606, longitude=2.3376, categoria="Cultura")
        self.gerar(self.nova_viagem())
        self.assertEqual(Local.objects.get(nome="Museu do Louvre").categoria, "Cultura")

    def test_lista_de_viagens_informa_total_de_atividades_e_categorias(self):
        vazia = self.nova_viagem(destino="Brasília, Brasil")
        self.gerar(self.nova_viagem())
        por_destino = {v["destino"]: v for v in self.client.get("/api/viagens/").data}
        self.assertEqual(por_destino["Paris, França"]["total_atividades"], 9)
        self.assertIn("Arte", por_destino["Paris, França"]["categorias"])
        self.assertEqual(por_destino[vazia["destino"]]["total_atividades"], 0)
        self.assertEqual(por_destino[vazia["destino"]]["categorias"], [])

    def test_ritmo_tranquilo_gera_menos_atividades_por_dia(self):
        viagem = self.gerar(self.nova_viagem(estilo="Tranquilo")).data["viagem"]
        self.assertEqual(len(viagem["dias"][0]["atividades"]), 3)

    def test_gerar_de_novo_sem_confirmar_e_recusado(self):
        viagem = self.nova_viagem()
        self.gerar(viagem)
        resposta = self.gerar(viagem)
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("substituir", resposta.data["erro"])

    def test_gerar_de_novo_com_substituir_refaz_sem_duplicar_locais(self):
        viagem = self.nova_viagem()
        self.gerar(viagem)
        locais_antes = Local.objects.count()
        resposta = self.gerar(viagem, substituir=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Local.objects.count(), locais_antes, "os locais do catálogo são reaproveitados")
        self.assertEqual(AtividadeRoteiro.objects.filter(dia__viagem_id=viagem["id_viagem"]).count(), 9)

    def test_dois_usuarios_compartilham_o_mesmo_local_do_catalogo(self):
        self.gerar(self.nova_viagem())
        locais = Local.objects.count()
        outro = self.cadastrar("Rafael", "rafael@email.com", "outra-senha")
        self.autenticar(outro["token"])
        self.gerar(self.nova_viagem())
        self.assertEqual(Local.objects.count(), locais)

    @override_settings(IA_PROVEDOR="groq", GROQ_API_KEY="")
    def test_sem_chave_configurada_usa_a_reserva_e_avisa(self):
        resposta = self.gerar(self.nova_viagem())
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["geracao"]["provedor"], "Simulado")
        self.assertIn("não respondeu", resposta.data["geracao"]["aviso"])

    @override_settings(IA_PROVEDOR="groq", GROQ_API_KEY="", IA_RESERVA="nenhuma")
    def test_sem_reserva_a_falha_vira_503_e_nada_e_gravado(self):
        viagem = self.nova_viagem()
        resposta = self.gerar(viagem)
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(AtividadeRoteiro.objects.count(), 0)

    def test_usuario_nao_gera_roteiro_da_viagem_de_outro(self):
        viagem = self.nova_viagem()
        outro = self.cadastrar("Rafael", "rafael@email.com", "outra-senha")
        self.autenticar(outro["token"])
        self.assertEqual(self.gerar(viagem).status_code, 404)


@override_settings(IA_RESERVA="simulado")
class TestesDoServico(BaseDeTeste):
    """Testa o GeradorRoteiroService diretamente, com clientes falsos."""

    def test_falha_do_provedor_cai_na_reserva(self):
        from aplicacao.gerador_roteiro import GeradorRoteiroService
        from integracao.ia.simulado import ClienteIASimulado
        from persistencia.models import Viagem

        self.criar_viagem(dias=2, destino="Lisboa, Portugal")
        servico = GeradorRoteiroService(Viagem.objects.get(), cliente=ClienteQueFalha(), reserva=ClienteIASimulado())
        resultado = servico.gerar_roteiro()
        self.assertEqual(resultado.provedor, "Simulado")
        self.assertIsNotNone(resultado.aviso)

    def test_preferencias_entram_no_pedido_da_mais_forte_para_a_mais_fraca(self):
        from aplicacao.gerador_roteiro import GeradorRoteiroService
        from persistencia.models import Viagem

        preferencias = [
            {"categoria": "Natureza", "nivel_interesse": 2},
            {"categoria": "Gastronomia", "nivel_interesse": 5},
        ]
        self.criar_viagem(dias=2, preferencias=preferencias)
        pedido = GeradorRoteiroService(Viagem.objects.get(), cliente=ClienteQueFalha()).montar_prompt()
        self.assertEqual(pedido.preferencias, [("Gastronomia", 5), ("Natureza", 2)])
        self.assertEqual(pedido.total_de_dias, 2)
