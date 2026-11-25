"""
Autenticação da API.

O login devolve um token assinado com a SECRET_KEY do servidor. O cliente
guarda esse token e o envia em todas as requisições seguintes, no cabeçalho:

    Authorization: Bearer <token>

O token carrega apenas o identificador do usuário. Como é assinado, não pode
ser alterado pelo cliente sem que a assinatura deixe de conferir. Também
expira após o prazo definido em VALIDADE_DO_TOKEN.

Por que não o sistema de autenticação padrão do Django? Ele exige a tabela
auth_user, que não existe no modelo físico aprovado (Figura 5). Usar a tabela
usuario do esquema mantém o banco de dados exatamente como foi modelado.
"""

from django.conf import settings
from django.core import signing
from rest_framework import authentication, exceptions

SAL_DO_TOKEN = "tripscripter.token-de-acesso"


def gerar_token(usuario):
    return signing.dumps({"id": usuario.id_usuario}, salt=SAL_DO_TOKEN)


def ler_token(token):
    """Devolve o id do usuário contido no token, ou lança AuthenticationFailed."""
    try:
        dados = signing.loads(token, salt=SAL_DO_TOKEN, max_age=settings.VALIDADE_DO_TOKEN)
    except signing.SignatureExpired:
        raise exceptions.AuthenticationFailed("Sessão expirada. Entre novamente.")
    except signing.BadSignature:
        raise exceptions.AuthenticationFailed("Token de acesso inválido.")
    return dados["id"]


class AutenticacaoPorToken(authentication.BaseAuthentication):
    """Identifica o usuário a partir do cabeçalho Authorization: Bearer <token>."""

    palavra_chave = "Bearer"

    def authenticate(self, request):
        # Importação local: a camada comum não depende da persistência no
        # carregamento do módulo, só no momento do uso.
        from persistencia.models import Usuario

        cabecalho = authentication.get_authorization_header(request).decode()
        partes = cabecalho.split()
        if not partes or partes[0] != self.palavra_chave:
            return None  # sem token: a permissão decide se a rota é pública
        if len(partes) != 2:
            raise exceptions.AuthenticationFailed("Cabeçalho Authorization malformado.")

        id_usuario = ler_token(partes[1])
        try:
            usuario = Usuario.objects.get(pk=id_usuario)
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed("Usuário não encontrado.")
        return usuario, partes[1]

    def authenticate_header(self, request):
        # Faz a API responder 401 (e não 403) quando falta o token.
        return self.palavra_chave
