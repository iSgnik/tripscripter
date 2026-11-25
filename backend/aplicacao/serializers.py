"""
Serializers (DTOs): convertem os models em JSON e validam os dados recebidos.

Os nomes dos campos acompanham as colunas do banco, para que quem lê o JSON
reconheça imediatamente a tabela de origem.
"""

from rest_framework import serializers

from dominio import regras
from persistencia.models import AtividadeRoteiro, DiaRoteiro, Local, NotaPessoal, Usuario, Viagem

# -----------------------------------------------------------------------------
# Usuário
# -----------------------------------------------------------------------------


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id_usuario", "nome", "email", "data_cadastro"]


class CadastroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=150)
    # Mesma regra de tamanho mínimo validada no front-end (js/cadastro.js).
    senha = serializers.CharField(min_length=8, max_length=128, write_only=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)


# -----------------------------------------------------------------------------
# Preferências
# -----------------------------------------------------------------------------


class PreferenciaSerializer(serializers.Serializer):
    categoria = serializers.ChoiceField(choices=regras.CATEGORIAS)
    nivel_interesse = serializers.IntegerField(min_value=regras.NIVEL_MINIMO, max_value=regras.NIVEL_MAXIMO)


def validar_categorias_unicas(preferencias):
    categorias = [p["categoria"] for p in preferencias]
    if len(categorias) != len(set(categorias)):
        raise serializers.ValidationError("Cada categoria pode aparecer uma única vez.")
    return preferencias


class ListaDePreferenciasSerializer(serializers.Serializer):
    preferencias = PreferenciaSerializer(many=True)

    def validate_preferencias(self, valor):
        return validar_categorias_unicas(valor)


# -----------------------------------------------------------------------------
# Roteiro
# -----------------------------------------------------------------------------


class LocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Local
        fields = ["id_local", "nome", "endereco", "latitude", "longitude", "horario_funcionamento", "categoria"]


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaPessoal
        fields = ["id_nota", "texto", "criado_em"]
        read_only_fields = ["id_nota", "criado_em"]

    def validate_texto(self, valor):
        if not valor.strip():
            raise serializers.ValidationError("A nota não pode ficar vazia.")
        return valor


class AtividadeSerializer(serializers.ModelSerializer):
    local = LocalSerializer(read_only=True)
    notas = NotaSerializer(many=True, read_only=True)

    class Meta:
        model = AtividadeRoteiro
        fields = ["id_atividade", "ordem_do_dia", "hora_sugerida", "custo_estimado", "local", "notas"]
        read_only_fields = ["id_atividade", "ordem_do_dia"]


class DiaSerializer(serializers.ModelSerializer):
    atividades = AtividadeSerializer(many=True, read_only=True)

    class Meta:
        model = DiaRoteiro
        fields = ["id_dia", "ordem", "data", "atividades"]


class ViagemResumoSerializer(serializers.ModelSerializer):
    """
    Usado nas listas (viagens e histórico), sem os dias.

    total_atividades e categorias vêm prontos da consulta quando a view usa
    com_resumo() (uma única consulta para a lista inteira). Fora das listas,
    são calculados aqui.
    """

    duracao = serializers.IntegerField(source="calcular_duracao", read_only=True)
    total_atividades = serializers.SerializerMethodField()
    categorias = serializers.SerializerMethodField()

    class Meta:
        model = Viagem
        fields = [
            "id_viagem", "destino", "data_inicio", "data_fim", "estilo_viagem",
            "duracao", "total_atividades", "categorias",
        ]

    def get_total_atividades(self, viagem):
        if hasattr(viagem, "total_atividades"):
            return viagem.total_atividades
        return AtividadeRoteiro.objects.filter(dia__viagem=viagem).count()

    def get_categorias(self, viagem):
        if hasattr(viagem, "categorias_dos_locais"):
            return sorted(c for c in viagem.categorias_dos_locais if c)
        return sorted(
            Local.objects.filter(atividades__dia__viagem=viagem, categoria__isnull=False)
            .values_list("categoria", flat=True)
            .distinct()
        )


class ViagemDetalheSerializer(ViagemResumoSerializer):
    """Usado na tela de roteiro e no mapa: a viagem com todos os dias e atividades."""

    dias = DiaSerializer(many=True, read_only=True)

    class Meta(ViagemResumoSerializer.Meta):
        fields = ViagemResumoSerializer.Meta.fields + ["dias"]


# -----------------------------------------------------------------------------
# Entradas dos casos de uso
# -----------------------------------------------------------------------------


class CriacaoDeViagemSerializer(serializers.Serializer):
    destino = serializers.CharField(max_length=120)
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()
    estilo_viagem = serializers.ChoiceField(choices=regras.ESTILOS, required=False, allow_null=True)
    preferencias = PreferenciaSerializer(many=True, required=False)

    def validate_preferencias(self, valor):
        return validar_categorias_unicas(valor)


class EdicaoDeViagemSerializer(serializers.Serializer):
    """
    Só destino e estilo podem ser alterados. Mudar as datas exigiria refazer
    os dias do roteiro e decidir o que fazer com as atividades de dias que
    deixariam de existir — decisão que ainda não foi tomada pela equipe.
    """

    destino = serializers.CharField(max_length=120, required=False)
    estilo_viagem = serializers.ChoiceField(choices=regras.ESTILOS, required=False, allow_null=True)


class GeracaoDeRoteiroSerializer(serializers.Serializer):
    substituir = serializers.BooleanField(default=False)


class ReaproveitamentoSerializer(serializers.Serializer):
    data_inicio = serializers.DateField()


class NovoLocalSerializer(serializers.ModelSerializer):
    categoria = serializers.ChoiceField(choices=regras.CATEGORIAS, required=False, allow_null=True)

    class Meta:
        model = Local
        fields = ["nome", "endereco", "latitude", "longitude", "horario_funcionamento", "categoria"]


class CriacaoDeAtividadeSerializer(serializers.Serializer):
    """Informe id_local (local do catálogo) ou local (novo local, incluído à mão)."""

    id_local = serializers.IntegerField(required=False)
    local = NovoLocalSerializer(required=False)
    hora_sugerida = serializers.TimeField(required=False, allow_null=True)
    custo_estimado = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True
    )

    def validate(self, dados):
        if ("id_local" in dados) == ("local" in dados):
            raise serializers.ValidationError("Informe id_local ou local, um dos dois.")
        return dados


class EdicaoDeAtividadeSerializer(serializers.Serializer):
    hora_sugerida = serializers.TimeField(required=False, allow_null=True)
    custo_estimado = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True
    )


class ReordenacaoSerializer(serializers.Serializer):
    ordem = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
