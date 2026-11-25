"""
Service Layer: um serviço por caso de uso.

Cada função que grava mais de uma tabela roda dentro de uma transação
(transaction.atomic). Se qualquer passo falhar, nada é gravado — por exemplo,
não fica uma viagem sem os seus dias.
"""

from django.db import transaction
from django.db.models import F, Max

from comum.excecoes import RegraDeNegocioViolada
from dominio import regras
from persistencia.models import (
    AtividadeRoteiro,
    DiaRoteiro,
    Local,
    NotaPessoal,
    Preferencia,
    Usuario,
    Viagem,
)

# -----------------------------------------------------------------------------
# Usuário (RQ001, RQ002)
# -----------------------------------------------------------------------------


def cadastrar_usuario(nome, email, senha):
    email = email.strip().lower()
    if Usuario.objects.filter(email=email).exists():
        raise RegraDeNegocioViolada("Já existe uma conta com este e-mail.")
    usuario = Usuario(nome=nome.strip(), email=email)
    usuario.definir_senha(senha)
    usuario.save()
    return usuario


def autenticar(email, senha):
    """Devolve o usuário se e-mail e senha conferem; senão, None."""
    usuario = Usuario.objects.filter(email=email.strip().lower()).first()
    if usuario is None or not usuario.autenticar(senha):
        return None
    return usuario


# -----------------------------------------------------------------------------
# Preferências (RQ003, RQ004)
# -----------------------------------------------------------------------------


@transaction.atomic
def salvar_preferencias(usuario, preferencias):
    """
    Substitui o conjunto de preferências do usuário.

    preferencias: lista de {"categoria": str, "nivel_interesse": int}.
    """
    usuario.preferencias.all().delete()
    Preferencia.objects.bulk_create(
        Preferencia(usuario=usuario, categoria=p["categoria"], nivel_interesse=p["nivel_interesse"])
        for p in preferencias
    )
    return list(usuario.preferencias.all())


# -----------------------------------------------------------------------------
# Viagem (RQ003, RQ011)
# -----------------------------------------------------------------------------


@transaction.atomic
def criar_viagem(usuario, destino, data_inicio, data_fim, estilo_viagem=None, preferencias=None):
    """Cria a viagem e um dia de roteiro, ainda vazio, para cada data do período."""
    regras.validar_periodo(data_inicio, data_fim)

    viagem = Viagem.objects.create(
        usuario=usuario,
        destino=destino.strip(),
        data_inicio=data_inicio,
        data_fim=data_fim,
        estilo_viagem=estilo_viagem,
    )
    DiaRoteiro.objects.bulk_create(
        DiaRoteiro(viagem=viagem, data=data, ordem=posicao)
        for posicao, data in enumerate(regras.datas_da_viagem(data_inicio, data_fim), start=1)
    )

    # O modelo guarda preferências por usuário, não por viagem. As escolhidas
    # no assistente passam a ser as preferências atuais do usuário.
    if preferencias is not None:
        salvar_preferencias(usuario, preferencias)

    return viagem


@transaction.atomic
def reaproveitar_viagem(viagem_original, data_inicio):
    """
    Cria uma nova viagem com o mesmo roteiro de outra, começando em outra data
    (RQ011: reaproveitar roteiros já criados). As notas pessoais não são
    copiadas, porque se referem à experiência da viagem original.
    """
    data_fim = data_inicio + (viagem_original.data_fim - viagem_original.data_inicio)
    datas = regras.datas_da_viagem(data_inicio, data_fim)

    nova = Viagem.objects.create(
        usuario=viagem_original.usuario,
        destino=viagem_original.destino,
        data_inicio=datas[0],
        data_fim=datas[-1],
        estilo_viagem=viagem_original.estilo_viagem,
    )
    dias_originais = viagem_original.dias.prefetch_related("atividades").order_by("ordem")
    for dia_original, data in zip(dias_originais, datas):
        novo_dia = DiaRoteiro.objects.create(viagem=nova, data=data, ordem=dia_original.ordem)
        AtividadeRoteiro.objects.bulk_create(
            AtividadeRoteiro(
                dia=novo_dia,
                local_id=a.local_id,  # o local do catálogo é reaproveitado, não copiado
                hora_sugerida=a.hora_sugerida,
                ordem_do_dia=a.ordem_do_dia,
                custo_estimado=a.custo_estimado,
            )
            for a in dia_original.atividades.all()
        )
    return nova


# -----------------------------------------------------------------------------
# Edição do roteiro (RQ005, RQ007)
# -----------------------------------------------------------------------------


def _obter_ou_criar_local(id_local=None, dados_local=None):
    if id_local is not None:
        try:
            return Local.objects.get(pk=id_local)
        except Local.DoesNotExist:
            raise RegraDeNegocioViolada("Local não encontrado no catálogo.")
    # Local incluído manualmente pelo usuário. Fica sem coordenadas até haver
    # geocodificação, e por isso ainda não aparece no mapa.
    return Local.objects.create(**dados_local)


@transaction.atomic
def adicionar_atividade(dia, id_local=None, dados_local=None, hora_sugerida=None, custo_estimado=None):
    """Inclui uma atividade ao final do dia."""
    local = _obter_ou_criar_local(id_local, dados_local)
    ultima = dia.atividades.aggregate(maior=Max("ordem_do_dia"))["maior"] or 0
    return AtividadeRoteiro.objects.create(
        dia=dia,
        local=local,
        hora_sugerida=hora_sugerida,
        ordem_do_dia=ultima + 1,
        custo_estimado=custo_estimado,
    )


def _aplicar_ordem(dia, ids_na_ordem):
    """
    Grava a nova posição de cada atividade.

    A restrição uq_atividade_ordem impede duas atividades na mesma posição,
    inclusive durante a troca. Por isso a gravação ocorre em duas etapas:
    primeiro todas são deslocadas para posições livres (acima de 1000), depois
    cada uma recebe a posição final. Posições negativas não servem, porque o
    esquema exige ordem_do_dia > 0.
    """
    dia.atividades.update(ordem_do_dia=F("ordem_do_dia") + 1000)
    for posicao, id_atividade in enumerate(ids_na_ordem, start=1):
        AtividadeRoteiro.objects.filter(pk=id_atividade, dia=dia).update(ordem_do_dia=posicao)


@transaction.atomic
def reordenar_atividades(dia, ids_na_nova_ordem):
    ids_atuais = list(dia.atividades.values_list("id_atividade", flat=True))
    regras.validar_nova_ordem(ids_atuais, ids_na_nova_ordem)
    _aplicar_ordem(dia, ids_na_nova_ordem)


@transaction.atomic
def remover_atividade(atividade):
    """Remove a atividade e renumera as restantes, para não deixar buracos na ordem."""
    dia = atividade.dia
    atividade.delete()  # as notas da atividade saem junto (ON DELETE CASCADE)
    restantes = list(dia.atividades.order_by("ordem_do_dia").values_list("id_atividade", flat=True))
    _aplicar_ordem(dia, restantes)


# -----------------------------------------------------------------------------
# Notas pessoais (RQ008)
# -----------------------------------------------------------------------------


def adicionar_nota(atividade, texto):
    return NotaPessoal.objects.create(atividade=atividade, texto=texto.strip())
