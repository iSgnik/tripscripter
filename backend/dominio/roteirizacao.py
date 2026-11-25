"""
Validação da sugestão de roteiro devolvida pela IA (validarLocais, Figura 2).

Um modelo de linguagem pode errar o formato, inventar coordenadas fora do
planeta, repetir lugares ou sugerir mais atividades do que o pedido. Nada do
que ele devolve é gravado sem passar por aqui.

A regra geral é aproveitar o que estiver correto e descartar o resto, campo
a campo: uma coordenada inválida não derruba a atividade inteira, só deixa o
local sem posição no mapa. A sugestão só é recusada por completo se nenhuma
atividade puder ser aproveitada.
"""

import re
import unicodedata
from datetime import time
from decimal import Decimal, InvalidOperation

from comum.excecoes import RegraDeNegocioViolada

from .regras import CATEGORIAS

# Atividades por dia conforme o ritmo escolhido no assistente.
ATIVIDADES_POR_ESTILO = {"Tranquilo": 3, "Equilibrado": 4, "Intenso": 6}
ATIVIDADES_POR_DIA_PADRAO = 4

# Tamanhos máximos das colunas em banco/01-esquema.sql.
TAMANHO_NOME, TAMANHO_ENDERECO, TAMANHO_HORARIO = 150, 255, 120

FORMATO_HORA = re.compile(r"^\s*([01]?\d|2[0-3])[:h]([0-5]\d)\s*$")


class RespostaDeIAInvalida(RegraDeNegocioViolada):
    """A sugestão da IA não tem nenhuma atividade aproveitável."""


def atividades_por_dia(estilo):
    return ATIVIDADES_POR_ESTILO.get(estilo, ATIVIDADES_POR_DIA_PADRAO)


def _texto(valor, tamanho):
    if not isinstance(valor, str):
        return None
    valor = " ".join(valor.split())
    return valor[:tamanho] if valor else None


def _hora(valor):
    correspondencia = FORMATO_HORA.match(valor) if isinstance(valor, str) else None
    return time(int(correspondencia[1]), int(correspondencia[2])) if correspondencia else None


def _coordenadas(latitude, longitude):
    """As duas juntas ou nenhuma: meia coordenada não serve para o mapa."""
    try:
        latitude, longitude = Decimal(str(latitude)), Decimal(str(longitude))
    except (InvalidOperation, ValueError, TypeError):
        return None, None
    if not (latitude.is_finite() and longitude.is_finite()):
        return None, None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None, None
    # (0, 0) fica no oceano Atlântico: é o valor que o modelo devolve quando não sabe.
    if latitude == 0 and longitude == 0:
        return None, None
    return latitude.quantize(Decimal("0.000001")), longitude.quantize(Decimal("0.000001"))


def _custo(valor):
    if isinstance(valor, bool):
        return None
    try:
        custo = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not custo.is_finite() or custo < 0 or custo >= Decimal("100000000"):
        return None
    return custo.quantize(Decimal("0.01"))


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


_CATEGORIA_POR_CHAVE = {_sem_acento(c): c for c in CATEGORIAS}


def _categoria(valor):
    """Aceita 'cultura' ou 'Vida Noturna'; qualquer valor fora da lista vira nulo."""
    if not isinstance(valor, str):
        return None
    return _CATEGORIA_POR_CHAVE.get(_sem_acento(" ".join(valor.split())))


def _atividade(bruta):
    if not isinstance(bruta, dict):
        return None
    nome = _texto(bruta.get("nome"), TAMANHO_NOME)
    if nome is None:
        return None
    latitude, longitude = _coordenadas(bruta.get("latitude"), bruta.get("longitude"))
    return {
        "nome": nome,
        "endereco": _texto(bruta.get("endereco"), TAMANHO_ENDERECO),
        "latitude": latitude,
        "longitude": longitude,
        "horario_funcionamento": _texto(bruta.get("horario_funcionamento"), TAMANHO_HORARIO),
        "hora_sugerida": _hora(bruta.get("hora_sugerida")),
        "custo_estimado": _custo(bruta.get("custo_estimado")),
        "categoria": _categoria(bruta.get("categoria")),
    }


def validar_sugestao(sugestao, total_de_dias, maximo_por_dia):
    """
    Devolve uma lista com total_de_dias posições; cada posição é a lista de
    atividades daquele dia, já validadas e em ordem cronológica.
    """
    dias = [[] for _ in range(total_de_dias)]
    dias_brutos = sugestao.get("dias") if isinstance(sugestao, dict) else None
    if not isinstance(dias_brutos, list):
        raise RespostaDeIAInvalida("A sugestão da IA não trouxe a lista de dias.")

    nomes_usados = set()
    for posicao, dia_bruto in enumerate(dias_brutos, start=1):
        if not isinstance(dia_bruto, dict):
            continue
        # Usa o número informado pela IA; se faltar, a posição na lista.
        ordem = dia_bruto.get("ordem")
        ordem = ordem if isinstance(ordem, int) and not isinstance(ordem, bool) else posicao
        if not 1 <= ordem <= total_de_dias:
            continue  # dia além do período da viagem

        atividades = dia_bruto.get("atividades")
        for bruta in atividades if isinstance(atividades, list) else []:
            atividade = _atividade(bruta)
            if atividade is None or atividade["nome"].lower() in nomes_usados:
                continue  # sem nome ou lugar repetido
            if len(dias[ordem - 1]) >= maximo_por_dia:
                break
            nomes_usados.add(atividade["nome"].lower())
            dias[ordem - 1].append(atividade)

    if not any(dias):
        raise RespostaDeIAInvalida("A sugestão da IA não trouxe nenhuma atividade aproveitável.")

    # Ordem cronológica; atividades sem horário vão para o fim do dia.
    for atividades in dias:
        atividades.sort(key=lambda a: (a["hora_sugerida"] is None, a["hora_sugerida"] or time()))
    return dias
