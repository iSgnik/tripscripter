"""
Executor dos testes automatizados.

Normalmente o Django cria o banco de testes rodando as migrations. Este
projeto não tem migrations, porque a estrutura vem do 01-esquema.sql. Então
o executor cria o banco de testes vazio e roda nele o mesmo script SQL que a
equipe usa no banco real. Assim os testes verificam o esquema verdadeiro, com
todas as restrições do PostgreSQL.
"""

from django.conf import settings
from django.db import connections
from django.test.runner import DiscoverRunner


class ExecutorDeTestesComEsquemaSQL(DiscoverRunner):
    def setup_databases(self, **kwargs):
        configuracao = super().setup_databases(**kwargs)
        script = settings.ARQUIVO_ESQUEMA.read_text(encoding="utf-8")
        with connections["default"].cursor() as cursor:
            cursor.execute(script)
        return configuracao
