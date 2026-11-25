"""Regras de negócio da criação e da organização de roteiros."""

from datetime import timedelta

from comum.excecoes import RegraDeNegocioViolada

# Mesmos interesses oferecidos no assistente de nova viagem e no protótipo.
# Os dados de exemplo (banco/02-dados-exemplo.sql) usam parte deles.
CATEGORIAS = (
    "Cultura", "Gastronomia", "Arte", "Natureza", "História", "Compras", "Vida noturna", "Praia",
)
ESTILOS = ("Tranquilo", "Equilibrado", "Intenso")

# Limite de duração de uma viagem. Sem ele, um período digitado errado
# (2026 → 2062) geraria milhares de dias e chamadas à IA.
DURACAO_MAXIMA_EM_DIAS = 30

NIVEL_MINIMO, NIVEL_MAXIMO = 1, 5


def validar_periodo(data_inicio, data_fim):
    if data_fim < data_inicio:
        raise RegraDeNegocioViolada("A data de término não pode ser anterior à de início.")
    duracao = (data_fim - data_inicio).days + 1
    if duracao > DURACAO_MAXIMA_EM_DIAS:
        raise RegraDeNegocioViolada(
            f"A viagem pode ter no máximo {DURACAO_MAXIMA_EM_DIAS} dias; foram informados {duracao}."
        )


def datas_da_viagem(data_inicio, data_fim):
    """Lista cada data do período, na ordem. Um dia de roteiro para cada."""
    total = (data_fim - data_inicio).days + 1
    return [data_inicio + timedelta(days=i) for i in range(total)]


def validar_nova_ordem(ids_atuais, ids_na_nova_ordem):
    """
    Confere se a nova ordem contém exatamente as atividades do dia, cada uma
    uma única vez. Impede que a reordenação perca ou duplique atividades.
    """
    if sorted(ids_atuais) != sorted(ids_na_nova_ordem):
        raise RegraDeNegocioViolada(
            "A nova ordem deve conter todas as atividades do dia, cada uma uma única vez."
        )
