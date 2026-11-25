"""
Views da API REST: o papel de Controller no MVC (Quadro 1 do documento).

Cada view segue o mesmo roteiro: valida a entrada com um serializer, chama o
serviço correspondente e devolve o resultado serializado.

Toda consulta é filtrada pelo usuário autenticado. Um usuário que tente abrir
a viagem de outro recebe 404, como se ela não existisse — responder 403
confirmaria que aquele identificador existe.
"""

from datetime import date

from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from comum.seguranca import gerar_token
from dominio import regras
from persistencia.models import AtividadeRoteiro, DiaRoteiro, Local, NotaPessoal, Viagem

from . import serializers as s
from . import servicos
from .gerador_roteiro import GeradorRoteiroService

# -----------------------------------------------------------------------------
# Funções auxiliares: buscam um registro garantindo que pertence ao usuário
# -----------------------------------------------------------------------------


def _viagem_do_usuario(request, id_viagem, com_roteiro=False):
    consulta = Viagem.objects.filter(usuario=request.user)
    if com_roteiro:
        # Carrega dias, atividades, locais e notas em poucas consultas, em vez
        # de uma consulta por atividade.
        consulta = consulta.prefetch_related(
            Prefetch(
                "dias",
                queryset=DiaRoteiro.objects.prefetch_related(
                    Prefetch(
                        "atividades",
                        queryset=AtividadeRoteiro.objects.select_related("local").prefetch_related("notas"),
                    )
                ),
            )
        )
    return get_object_or_404(consulta, pk=id_viagem)


def com_resumo(consulta):
    """
    Acrescenta a cada viagem da lista o total de atividades e as categorias
    dos seus locais, em duas consultas para a lista inteira (e não duas por
    viagem). Usa só recursos comuns a todos os bancos, para funcionar também
    no modo de demonstração com SQLite.
    """
    viagens = list(consulta.annotate(total_atividades=Count("dias__atividades", distinct=True)))
    categorias = {v.pk: set() for v in viagens}
    pares = (
        Local.objects.filter(atividades__dia__viagem__in=viagens, categoria__isnull=False)
        .values_list("atividades__dia__viagem_id", "categoria")
        .distinct()
    )
    for id_viagem, categoria in pares:
        categorias[id_viagem].add(categoria)
    for viagem in viagens:
        viagem.categorias_dos_locais = categorias[viagem.pk]
    return viagens


def _dia_do_usuario(request, id_dia):
    return get_object_or_404(DiaRoteiro, pk=id_dia, viagem__usuario=request.user)


def _atividade_do_usuario(request, id_atividade):
    return get_object_or_404(AtividadeRoteiro, pk=id_atividade, dia__viagem__usuario=request.user)


def _nota_do_usuario(request, id_nota):
    return get_object_or_404(NotaPessoal, pk=id_nota, atividade__dia__viagem__usuario=request.user)


def _validar(serializer_class, request, parcial=False):
    serializer = serializer_class(data=request.data, partial=parcial)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


# -----------------------------------------------------------------------------
# Rotas públicas
# -----------------------------------------------------------------------------


class Cadastro(APIView):
    """POST /api/auth/cadastro/ — cria a conta e já devolve o token (RQ001)."""

    permission_classes = [AllowAny]

    def post(self, request):
        dados = _validar(s.CadastroSerializer, request)
        usuario = servicos.cadastrar_usuario(dados["nome"], dados["email"], dados["senha"])
        return Response(
            {"usuario": s.UsuarioSerializer(usuario).data, "token": gerar_token(usuario)},
            status=status.HTTP_201_CREATED,
        )


class Login(APIView):
    """POST /api/auth/login/ — confere e-mail e senha e devolve o token (RQ002)."""

    permission_classes = [AllowAny]

    def post(self, request):
        dados = _validar(s.LoginSerializer, request)
        usuario = servicos.autenticar(dados["email"], dados["senha"])
        if usuario is None:
            # Mesma mensagem para e-mail inexistente e senha errada, para não
            # revelar quais e-mails têm conta.
            return Response({"erro": "E-mail ou senha incorretos."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"usuario": s.UsuarioSerializer(usuario).data, "token": gerar_token(usuario)})


class Opcoes(APIView):
    """GET /api/opcoes/ — categorias e estilos aceitos, para montar os formulários."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "categorias": regras.CATEGORIAS,
                "estilos": regras.ESTILOS,
                "nivel_interesse": {"minimo": regras.NIVEL_MINIMO, "maximo": regras.NIVEL_MAXIMO},
                "duracao_maxima_em_dias": regras.DURACAO_MAXIMA_EM_DIAS,
            }
        )


# -----------------------------------------------------------------------------
# Usuário e preferências
# -----------------------------------------------------------------------------


class UsuarioAtual(APIView):
    """GET /api/usuario/ — dados de quem está autenticado."""

    def get(self, request):
        return Response(s.UsuarioSerializer(request.user).data)


class Preferencias(APIView):
    """GET e PUT /api/preferencias/ — PUT substitui o conjunto inteiro."""

    def get(self, request):
        preferencias = request.user.preferencias.order_by("categoria")
        return Response({"preferencias": s.PreferenciaSerializer(preferencias, many=True).data})

    def put(self, request):
        dados = _validar(s.ListaDePreferenciasSerializer, request)
        preferencias = servicos.salvar_preferencias(request.user, dados["preferencias"])
        return Response({"preferencias": s.PreferenciaSerializer(preferencias, many=True).data})


# -----------------------------------------------------------------------------
# Viagens
# -----------------------------------------------------------------------------


class Viagens(APIView):
    """GET /api/viagens/ — viagens em andamento ou futuras. POST — cria (RQ003)."""

    def get(self, request):
        viagens = com_resumo(Viagem.objects.filter(usuario=request.user, data_fim__gte=date.today()))
        return Response(s.ViagemResumoSerializer(viagens, many=True).data)

    def post(self, request):
        dados = _validar(s.CriacaoDeViagemSerializer, request)
        viagem = servicos.criar_viagem(request.user, **dados)
        viagem = _viagem_do_usuario(request, viagem.pk, com_roteiro=True)
        return Response(s.ViagemDetalheSerializer(viagem).data, status=status.HTTP_201_CREATED)


class Historico(APIView):
    """GET /api/viagens/historico/ — viagens encerradas, da mais recente à mais antiga (RQ011)."""

    def get(self, request):
        viagens = com_resumo(
            Viagem.objects.filter(usuario=request.user, data_fim__lt=date.today()).order_by("-data_fim")
        )
        return Response(s.ViagemResumoSerializer(viagens, many=True).data)


class ViagemDetalhe(APIView):
    """GET, PATCH e DELETE /api/viagens/<id>/ — o roteiro completo (RQ005, RQ006)."""

    def get(self, request, id_viagem):
        return Response(s.ViagemDetalheSerializer(_viagem_do_usuario(request, id_viagem, com_roteiro=True)).data)

    def patch(self, request, id_viagem):
        viagem = _viagem_do_usuario(request, id_viagem)
        dados = _validar(s.EdicaoDeViagemSerializer, request, parcial=True)
        for campo, valor in dados.items():
            setattr(viagem, campo, valor)
        viagem.save()
        return Response(s.ViagemResumoSerializer(viagem).data)

    def delete(self, request, id_viagem):
        # Dias, atividades e notas saem junto (ON DELETE CASCADE no esquema).
        _viagem_do_usuario(request, id_viagem).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GerarRoteiro(APIView):
    """
    POST /api/viagens/<id>/gerar-roteiro/ — preenche os dias com a sugestão da IA (RQ004).

    Se o roteiro já tiver atividades, exige {"substituir": true}, porque a
    geração apaga as atividades e as notas atuais.
    """

    def post(self, request, id_viagem):
        viagem = _viagem_do_usuario(request, id_viagem)
        dados = _validar(s.GeracaoDeRoteiroSerializer, request)
        resultado = GeradorRoteiroService(viagem).gerar_roteiro(substituir=dados["substituir"])
        viagem = _viagem_do_usuario(request, id_viagem, com_roteiro=True)
        return Response(
            {
                "geracao": {
                    "provedor": resultado.provedor,
                    "aviso": resultado.aviso,
                    "tempo_em_ms": resultado.tempo_em_ms,
                    "total_de_atividades": resultado.total_de_atividades,
                },
                "viagem": s.ViagemDetalheSerializer(viagem).data,
            }
        )


class ReaproveitarViagem(APIView):
    """POST /api/viagens/<id>/reaproveitar/ — nova viagem com o mesmo roteiro (RQ011)."""

    def post(self, request, id_viagem):
        original = _viagem_do_usuario(request, id_viagem)
        dados = _validar(s.ReaproveitamentoSerializer, request)
        nova = servicos.reaproveitar_viagem(original, dados["data_inicio"])
        nova = _viagem_do_usuario(request, nova.pk, com_roteiro=True)
        return Response(s.ViagemDetalheSerializer(nova).data, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------------------------
# Atividades (RQ007)
# -----------------------------------------------------------------------------


class AtividadesDoDia(APIView):
    """POST /api/dias/<id>/atividades/ — inclui uma atividade ao final do dia."""

    def post(self, request, id_dia):
        dia = _dia_do_usuario(request, id_dia)
        dados = _validar(s.CriacaoDeAtividadeSerializer, request)
        atividade = servicos.adicionar_atividade(
            dia,
            id_local=dados.get("id_local"),
            dados_local=dados.get("local"),
            hora_sugerida=dados.get("hora_sugerida"),
            custo_estimado=dados.get("custo_estimado"),
        )
        return Response(s.AtividadeSerializer(atividade).data, status=status.HTTP_201_CREATED)


class ReordenarDia(APIView):
    """POST /api/dias/<id>/reordenar/ — recebe os ids das atividades na nova ordem."""

    def post(self, request, id_dia):
        dia = _dia_do_usuario(request, id_dia)
        dados = _validar(s.ReordenacaoSerializer, request)
        servicos.reordenar_atividades(dia, dados["ordem"])
        atividades = dia.atividades.select_related("local").prefetch_related("notas")
        return Response(s.AtividadeSerializer(atividades, many=True).data)


class AtividadeDetalhe(APIView):
    """PATCH e DELETE /api/atividades/<id>/."""

    def patch(self, request, id_atividade):
        atividade = _atividade_do_usuario(request, id_atividade)
        dados = _validar(s.EdicaoDeAtividadeSerializer, request, parcial=True)
        for campo, valor in dados.items():
            setattr(atividade, campo, valor)
        atividade.save()
        return Response(s.AtividadeSerializer(atividade).data)

    def delete(self, request, id_atividade):
        servicos.remover_atividade(_atividade_do_usuario(request, id_atividade))
        return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Notas pessoais (RQ008)
# -----------------------------------------------------------------------------


class NotasDaAtividade(APIView):
    """GET e POST /api/atividades/<id>/notas/."""

    def get(self, request, id_atividade):
        atividade = _atividade_do_usuario(request, id_atividade)
        return Response(s.NotaSerializer(atividade.notas.all(), many=True).data)

    def post(self, request, id_atividade):
        atividade = _atividade_do_usuario(request, id_atividade)
        dados = _validar(s.NotaSerializer, request)
        nota = servicos.adicionar_nota(atividade, dados["texto"])
        return Response(s.NotaSerializer(nota).data, status=status.HTTP_201_CREATED)


class NotaDetalhe(APIView):
    """PATCH e DELETE /api/notas/<id>/."""

    def patch(self, request, id_nota):
        nota = _nota_do_usuario(request, id_nota)
        dados = _validar(s.NotaSerializer, request)
        nota.texto = dados["texto"].strip()
        nota.save()
        return Response(s.NotaSerializer(nota).data)

    def delete(self, request, id_nota):
        _nota_do_usuario(request, id_nota).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
