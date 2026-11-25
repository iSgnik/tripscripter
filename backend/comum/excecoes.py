"""
Tratamento uniforme de erros da API.

Toda resposta de erro tem o mesmo formato, para que o front-end trate todas
da mesma maneira:

    {"erro": "mensagem para o usuário", "detalhes": {...campos inválidos...}}
"""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class RegraDeNegocioViolada(Exception):
    """Lançada pela camada de domínio quando uma regra do negócio é violada."""


class ConflitoDeEstado(RegraDeNegocioViolada):
    """A operação não pode ser feita no estado atual do registro (HTTP 409)."""


class ServicoIndisponivel(Exception):
    """Um serviço externo falhou e não há alternativa configurada (HTTP 503)."""


def tratar_excecao(exc, contexto):
    if isinstance(exc, ConflitoDeEstado):
        return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, ServicoIndisponivel):
        return Response({"erro": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if isinstance(exc, RegraDeNegocioViolada):
        return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    # Restrição do banco que escapou da validação da aplicação. O detalhe
    # técnico do PostgreSQL não é mostrado ao usuário.
    if isinstance(exc, IntegrityError):
        return Response(
            {"erro": "Os dados violam uma regra de integridade do banco."},
            status=status.HTTP_409_CONFLICT,
        )

    resposta = exception_handler(exc, contexto)
    if resposta is None:
        return None

    dados = resposta.data
    if isinstance(dados, dict) and "detail" in dados:
        resposta.data = {"erro": str(dados["detail"])}
    else:
        resposta.data = {"erro": "Dados inválidos.", "detalhes": dados}
    return resposta
