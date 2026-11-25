"""
Testes da API REST.

Cada teste roda num banco PostgreSQL temporário criado a partir do
banco/01-esquema.sql (ver comum/testes.py), e é desfeito ao final.

Execução:  python manage.py test
"""

from datetime import date, timedelta

from rest_framework.test import APITestCase

from persistencia.models import AtividadeRoteiro, DiaRoteiro, Local, NotaPessoal, Usuario, Viagem

HOJE = date.today()


class BaseDeTeste(APITestCase):
    """Cria um usuário autenticado e oferece atalhos para as chamadas mais comuns."""

    def setUp(self):
        self.token = self.cadastrar("Marina Alves", "marina@email.com", "senha-segura")["token"]
        self.autenticar(self.token)

    def cadastrar(self, nome, email, senha):
        resposta = self.client.post("/api/auth/cadastro/", {"nome": nome, "email": email, "senha": senha}, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        return resposta.data

    def autenticar(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def criar_viagem(self, dias=3, inicio=None, **extra):
        inicio = inicio or HOJE + timedelta(days=10)
        corpo = {
            "destino": "Lisboa, Portugal",
            "data_inicio": inicio.isoformat(),
            "data_fim": (inicio + timedelta(days=dias - 1)).isoformat(),
            "estilo_viagem": "Equilibrado",
            **extra,
        }
        return self.client.post("/api/viagens/", corpo, format="json")

    def adicionar_local_manual(self, id_dia, nome):
        resposta = self.client.post(f"/api/dias/{id_dia}/atividades/", {"local": {"nome": nome}}, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        return resposta.data


# -----------------------------------------------------------------------------
# RQ001 e RQ002 — cadastro e login
# -----------------------------------------------------------------------------


class TestesDeAcesso(BaseDeTeste):
    def test_senha_e_guardada_como_resumo_e_nunca_em_texto(self):
        usuario = Usuario.objects.get(email="marina@email.com")
        self.assertNotIn("senha-segura", usuario.senha_hash)
        self.assertTrue(usuario.senha_hash.startswith("pbkdf2_sha256$"))

    def test_email_repetido_e_recusado(self):
        resposta = self.client.post(
            "/api/auth/cadastro/", {"nome": "Outra", "email": "MARINA@email.com", "senha": "12345678"}, format="json"
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("e-mail", resposta.data["erro"])

    def test_senha_curta_e_recusada(self):
        resposta = self.client.post(
            "/api/auth/cadastro/", {"nome": "Rafa", "email": "rafa@email.com", "senha": "123"}, format="json"
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("senha", resposta.data["detalhes"])

    def test_login_com_senha_correta_devolve_token(self):
        self.client.credentials()
        resposta = self.client.post("/api/auth/login/", {"email": "marina@email.com", "senha": "senha-segura"}, format="json")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("token", resposta.data)

    def test_login_com_senha_errada_e_recusado_sem_revelar_o_motivo(self):
        errada = self.client.post("/api/auth/login/", {"email": "marina@email.com", "senha": "outra"}, format="json")
        inexistente = self.client.post("/api/auth/login/", {"email": "nao@existe.com", "senha": "outra"}, format="json")
        self.assertEqual(errada.status_code, 401)
        self.assertEqual(errada.data, inexistente.data)

    def test_rotas_protegidas_exigem_token(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/viagens/").status_code, 401)

    def test_token_adulterado_e_recusado(self):
        self.autenticar(self.token[:-3] + "xyz")
        self.assertEqual(self.client.get("/api/viagens/").status_code, 401)


# -----------------------------------------------------------------------------
# RQ003 — criação de viagem e preferências
# -----------------------------------------------------------------------------


class TestesDeViagem(BaseDeTeste):
    def test_viagem_nasce_com_um_dia_de_roteiro_por_data(self):
        resposta = self.criar_viagem(dias=4)
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data["duracao"], 4)
        self.assertEqual([d["ordem"] for d in resposta.data["dias"]], [1, 2, 3, 4])

    def test_periodo_invertido_e_recusado(self):
        corpo = {"destino": "Paris", "data_inicio": "2026-12-10", "data_fim": "2026-12-01"}
        resposta = self.client.post("/api/viagens/", corpo, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(Viagem.objects.count(), 0)

    def test_viagem_acima_do_limite_de_dias_e_recusada(self):
        self.assertEqual(self.criar_viagem(dias=31).status_code, 400)

    def test_estilo_fora_da_lista_e_recusado(self):
        self.assertEqual(self.criar_viagem(estilo_viagem="Radical").status_code, 400)

    def test_preferencias_do_assistente_sao_salvas_no_usuario(self):
        preferencias = [{"categoria": "Cultura", "nivel_interesse": 5}, {"categoria": "Natureza", "nivel_interesse": 2}]
        self.criar_viagem(preferencias=preferencias)
        resposta = self.client.get("/api/preferencias/")
        self.assertEqual(len(resposta.data["preferencias"]), 2)

    def test_preferencia_com_nivel_fora_da_escala_e_recusada(self):
        corpo = {"preferencias": [{"categoria": "Arte", "nivel_interesse": 9}]}
        self.assertEqual(self.client.put("/api/preferencias/", corpo, format="json").status_code, 400)

    def test_categoria_repetida_e_recusada(self):
        corpo = {"preferencias": [{"categoria": "Arte", "nivel_interesse": 3}, {"categoria": "Arte", "nivel_interesse": 4}]}
        self.assertEqual(self.client.put("/api/preferencias/", corpo, format="json").status_code, 400)

    def test_apagar_viagem_remove_dias_atividades_e_notas(self):
        viagem = self.criar_viagem(dias=2).data
        atividade = self.adicionar_local_manual(viagem["dias"][0]["id_dia"], "Castelo de São Jorge")
        self.client.post(f"/api/atividades/{atividade['id_atividade']}/notas/", {"texto": "Ir cedo"}, format="json")

        self.assertEqual(self.client.delete(f"/api/viagens/{viagem['id_viagem']}/").status_code, 204)
        self.assertEqual(DiaRoteiro.objects.count(), 0)
        self.assertEqual(AtividadeRoteiro.objects.count(), 0)
        self.assertEqual(NotaPessoal.objects.count(), 0)
        self.assertEqual(Local.objects.count(), 1, "o catálogo de locais é preservado")


# -----------------------------------------------------------------------------
# RQ005 e RQ007 — organização e edição do roteiro
# -----------------------------------------------------------------------------


class TestesDeRoteiro(BaseDeTeste):
    def setUp(self):
        super().setUp()
        self.viagem = self.criar_viagem(dias=2).data
        self.id_dia = self.viagem["dias"][0]["id_dia"]
        self.ids = [
            self.adicionar_local_manual(self.id_dia, nome)["id_atividade"]
            for nome in ("Torre de Belém", "Mosteiro dos Jerónimos", "LX Factory")
        ]

    def ordem_atual(self):
        return list(
            AtividadeRoteiro.objects.filter(dia_id=self.id_dia).order_by("ordem_do_dia").values_list("id_atividade", flat=True)
        )

    def test_atividades_entram_ao_final_do_dia(self):
        self.assertEqual(self.ordem_atual(), self.ids)

    def test_local_incluido_a_mao_fica_sem_coordenadas(self):
        local = Local.objects.get(nome="LX Factory")
        self.assertIsNone(local.latitude)

    def test_local_incluido_a_mao_aceita_categoria_da_lista(self):
        corpo = {"local": {"nome": "Feira da Ladra", "categoria": "Cultura"}}
        resposta = self.client.post(f"/api/dias/{self.id_dia}/atividades/", corpo, format="json")
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["local"]["categoria"], "Cultura")

    def test_local_incluido_a_mao_com_categoria_fora_da_lista_e_recusado(self):
        corpo = {"local": {"nome": "Estádio da Luz", "categoria": "Esportes"}}
        resposta = self.client.post(f"/api/dias/{self.id_dia}/atividades/", corpo, format="json")
        self.assertEqual(resposta.status_code, 400)

    def test_atividade_pode_usar_local_do_catalogo(self):
        local = Local.objects.create(nome="Oceanário de Lisboa", latitude=38.7635, longitude=-9.0937)
        resposta = self.client.post(f"/api/dias/{self.id_dia}/atividades/", {"id_local": local.pk}, format="json")
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["local"]["nome"], "Oceanário de Lisboa")

    def test_reordenar_inverte_a_ordem_sem_violar_a_restricao_de_unicidade(self):
        nova = list(reversed(self.ids))
        resposta = self.client.post(f"/api/dias/{self.id_dia}/reordenar/", {"ordem": nova}, format="json")
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(self.ordem_atual(), nova)

    def test_reordenar_com_atividade_faltando_e_recusado(self):
        resposta = self.client.post(f"/api/dias/{self.id_dia}/reordenar/", {"ordem": self.ids[:2]}, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.ordem_atual(), self.ids)

    def test_remover_renumera_as_restantes(self):
        self.client.delete(f"/api/atividades/{self.ids[0]}/")
        ordens = list(AtividadeRoteiro.objects.filter(dia_id=self.id_dia).order_by("ordem_do_dia").values_list("ordem_do_dia", flat=True))
        self.assertEqual(ordens, [1, 2])

    def test_custo_negativo_e_recusado(self):
        resposta = self.client.patch(f"/api/atividades/{self.ids[0]}/", {"custo_estimado": "-5.00"}, format="json")
        self.assertEqual(resposta.status_code, 400)

    def test_roteiro_completo_traz_dias_atividades_e_locais(self):
        resposta = self.client.get(f"/api/viagens/{self.viagem['id_viagem']}/")
        primeiro_dia = resposta.data["dias"][0]
        self.assertEqual([a["local"]["nome"] for a in primeiro_dia["atividades"]][0], "Torre de Belém")


# -----------------------------------------------------------------------------
# RQ008 — notas pessoais
# -----------------------------------------------------------------------------


class TestesDeNotas(BaseDeTeste):
    def setUp(self):
        super().setUp()
        viagem = self.criar_viagem(dias=1).data
        self.id_atividade = self.adicionar_local_manual(viagem["dias"][0]["id_dia"], "Alfama")["id_atividade"]

    def test_criar_editar_e_apagar_nota(self):
        nota = self.client.post(f"/api/atividades/{self.id_atividade}/notas/", {"texto": "Comer pastel de nata"}, format="json").data
        editada = self.client.patch(f"/api/notas/{nota['id_nota']}/", {"texto": "Dois pastéis"}, format="json")
        self.assertEqual(editada.data["texto"], "Dois pastéis")
        self.assertEqual(self.client.delete(f"/api/notas/{nota['id_nota']}/").status_code, 204)

    def test_nota_vazia_e_recusada(self):
        resposta = self.client.post(f"/api/atividades/{self.id_atividade}/notas/", {"texto": "   "}, format="json")
        self.assertEqual(resposta.status_code, 400)


# -----------------------------------------------------------------------------
# RQ011 — histórico e reaproveitamento
# -----------------------------------------------------------------------------


class TestesDeHistorico(BaseDeTeste):
    def test_viagens_encerradas_aparecem_so_no_historico(self):
        self.criar_viagem(dias=2, inicio=HOJE - timedelta(days=30))
        self.criar_viagem(dias=2, inicio=HOJE + timedelta(days=30))
        self.assertEqual(len(self.client.get("/api/viagens/").data), 1)
        self.assertEqual(len(self.client.get("/api/viagens/historico/").data), 1)

    def test_reaproveitar_copia_o_roteiro_para_novas_datas(self):
        antiga = self.criar_viagem(dias=2, inicio=HOJE - timedelta(days=60)).data
        self.adicionar_local_manual(antiga["dias"][1]["id_dia"], "Sintra")

        nova_data = HOJE + timedelta(days=90)
        resposta = self.client.post(
            f"/api/viagens/{antiga['id_viagem']}/reaproveitar/", {"data_inicio": nova_data.isoformat()}, format="json"
        )
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data["data_inicio"], nova_data.isoformat())
        self.assertEqual(resposta.data["dias"][1]["atividades"][0]["local"]["nome"], "Sintra")
        self.assertEqual(Local.objects.filter(nome="Sintra").count(), 1, "o local é reaproveitado, não duplicado")


# -----------------------------------------------------------------------------
# Isolamento entre usuários
# -----------------------------------------------------------------------------


class TestesDeIsolamento(BaseDeTeste):
    def test_usuario_nao_acessa_nem_altera_a_viagem_de_outro(self):
        viagem = self.criar_viagem().data
        id_dia = viagem["dias"][0]["id_dia"]

        outro = self.cadastrar("Rafael", "rafael@email.com", "outra-senha")
        self.autenticar(outro["token"])

        self.assertEqual(self.client.get(f"/api/viagens/{viagem['id_viagem']}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/viagens/{viagem['id_viagem']}/").status_code, 404)
        self.assertEqual(
            self.client.post(f"/api/dias/{id_dia}/atividades/", {"local": {"nome": "Invasão"}}, format="json").status_code, 404
        )
        self.assertEqual(self.client.get("/api/viagens/").data, [])
