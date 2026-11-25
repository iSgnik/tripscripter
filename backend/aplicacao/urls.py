from django.urls import path

from . import views

urlpatterns = [
    # Públicas
    path("auth/cadastro/", views.Cadastro.as_view()),
    path("auth/login/", views.Login.as_view()),
    path("opcoes/", views.Opcoes.as_view()),
    # Usuário
    path("usuario/", views.UsuarioAtual.as_view()),
    path("preferencias/", views.Preferencias.as_view()),
    # Viagens
    path("viagens/", views.Viagens.as_view()),
    path("viagens/historico/", views.Historico.as_view()),
    path("viagens/<int:id_viagem>/", views.ViagemDetalhe.as_view()),
    path("viagens/<int:id_viagem>/gerar-roteiro/", views.GerarRoteiro.as_view()),
    path("viagens/<int:id_viagem>/reaproveitar/", views.ReaproveitarViagem.as_view()),
    # Roteiro
    path("dias/<int:id_dia>/atividades/", views.AtividadesDoDia.as_view()),
    path("dias/<int:id_dia>/reordenar/", views.ReordenarDia.as_view()),
    path("atividades/<int:id_atividade>/", views.AtividadeDetalhe.as_view()),
    path("atividades/<int:id_atividade>/notas/", views.NotasDaAtividade.as_view()),
    path("notas/<int:id_nota>/", views.NotaDetalhe.as_view()),
]
