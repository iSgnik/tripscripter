"""
Models do TripScripter.

Cada classe corresponde a uma tabela de banco/01-esquema.sql, com os mesmos
nomes de tabela e de coluna. O esquema SQL é a fonte oficial da estrutura:

- managed = False impede o Django de criar, alterar ou apagar as tabelas;
- não existem migrations neste projeto;
- qualquer mudança de estrutura é feita primeiro no 01-esquema.sql e depois
  refletida aqui.

As restrições (CHECK, UNIQUE, chaves estrangeiras) são garantidas pelo banco.
A aplicação repete as validações mais importantes apenas para devolver ao
usuário uma mensagem clara, em vez de um erro do PostgreSQL.
"""

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Usuario(models.Model):
    """Dados de cadastro e credenciais de acesso do turista (RQ001, RQ002)."""

    id_usuario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=120)
    email = models.CharField(max_length=150, unique=True)
    senha_hash = models.CharField(max_length=255)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "usuario"

    def __str__(self):
        return self.email

    # A senha em texto puro nunca é guardada: só o resumo criptográfico.
    def definir_senha(self, senha):
        self.senha_hash = make_password(senha)

    def autenticar(self, senha):
        return check_password(senha, self.senha_hash)

    # O Django REST Framework consulta este atributo para decidir se a
    # requisição está autenticada. Todo Usuario carregado do banco está.
    @property
    def is_authenticated(self):
        return True


class Preferencia(models.Model):
    """Categoria de interesse do usuário e o nível de cada uma (RQ003, RQ004)."""

    id_preferencia = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, db_column="id_usuario", related_name="preferencias"
    )
    categoria = models.CharField(max_length=50)
    nivel_interesse = models.SmallIntegerField(default=3)

    class Meta:
        managed = False
        db_table = "preferencia"

    def descrever(self):
        return f"{self.categoria} (interesse {self.nivel_interesse} de 5)"


class Viagem(models.Model):
    """Destino, período e estilo de uma viagem planejada (RQ003)."""

    id_viagem = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, db_column="id_usuario", related_name="viagens"
    )
    destino = models.CharField(max_length=120)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    estilo_viagem = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "viagem"
        ordering = ["data_inicio"]

    def calcular_duracao(self):
        return (self.data_fim - self.data_inicio).days + 1


class DiaRoteiro(models.Model):
    """Cada dia da viagem e sua ordem dentro do roteiro (RQ005)."""

    id_dia = models.AutoField(primary_key=True)
    viagem = models.ForeignKey(
        Viagem, on_delete=models.CASCADE, db_column="id_viagem", related_name="dias"
    )
    data = models.DateField()
    ordem = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "dia_roteiro"
        ordering = ["ordem"]


class Local(models.Model):
    """Ponto turístico do catálogo, reaproveitado entre roteiros (RQ006)."""

    id_local = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    horario_funcionamento = models.CharField(max_length=120, null=True, blank=True)
    # Mesma classificação de Preferencia.categoria (dominio/regras.CATEGORIAS).
    categoria = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "local"

    def __str__(self):
        return self.nome


class AtividadeRoteiro(models.Model):
    """Atividade sugerida para um dia, com horário, ordem e custo (RQ005, RQ007)."""

    id_atividade = models.AutoField(primary_key=True)
    dia = models.ForeignKey(
        DiaRoteiro, on_delete=models.CASCADE, db_column="id_dia", related_name="atividades"
    )
    # O banco usa ON DELETE RESTRICT: um local em uso não pode ser apagado.
    local = models.ForeignKey(
        Local, on_delete=models.RESTRICT, db_column="id_local", related_name="atividades"
    )
    hora_sugerida = models.TimeField(null=True, blank=True)
    ordem_do_dia = models.SmallIntegerField()
    custo_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "atividade_roteiro"
        ordering = ["ordem_do_dia"]


class NotaPessoal(models.Model):
    """Anotação privada do usuário sobre uma atividade (RQ008)."""

    id_nota = models.AutoField(primary_key=True)
    atividade = models.ForeignKey(
        AtividadeRoteiro, on_delete=models.CASCADE, db_column="id_atividade", related_name="notas"
    )
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "nota_pessoal"
        ordering = ["criado_em"]
