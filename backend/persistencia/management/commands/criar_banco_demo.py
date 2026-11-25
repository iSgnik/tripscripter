"""
Cria o banco de demonstração em SQLite (modo DB_MOTOR=sqlite).

    python manage.py criar_banco_demo            cria, se ainda não existir
    python manage.py criar_banco_demo --recriar  apaga e cria de novo

As tabelas são criadas a partir dos models, que espelham banco/01-esquema.sql.
As restrições de unicidade do esquema são acrescentadas à parte, porque os
models não as declaram (no PostgreSQL, quem as garante é o próprio esquema).
Os dados vêm de persistencia/fixtures/dados_exemplo.json, gerado a partir de
banco/02-dados-exemplo.sql. Os dois usuários de exemplo entram com a senha
"demonstracao".
"""

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from persistencia import models

# Na ordem das dependências entre as tabelas.
MODELS = [
    models.Usuario,
    models.Preferencia,
    models.Viagem,
    models.DiaRoteiro,
    models.Local,
    models.AtividadeRoteiro,
    models.NotaPessoal,
]

# Mesmas restrições UNIQUE de banco/01-esquema.sql.
UNICIDADE = [
    "CREATE UNIQUE INDEX uq_preferencia_usuario_categoria ON preferencia (id_usuario, categoria)",
    "CREATE UNIQUE INDEX uq_dia_roteiro_ordem ON dia_roteiro (id_viagem, ordem)",
    "CREATE UNIQUE INDEX uq_dia_roteiro_data ON dia_roteiro (id_viagem, data)",
    "CREATE UNIQUE INDEX uq_atividade_ordem ON atividade_roteiro (id_dia, ordem_do_dia)",
]


class Command(BaseCommand):
    help = "Cria o banco de demonstração em SQLite, com os dados de exemplo."

    def add_arguments(self, parser):
        parser.add_argument("--recriar", action="store_true", help="Apaga o banco de demonstração e cria de novo.")

    def handle(self, *args, recriar=False, **opcoes):
        if settings.DB_MOTOR != "sqlite":
            raise CommandError("Este comando só vale no modo de demonstração. Defina DB_MOTOR=sqlite no .env.")

        arquivo = settings.DATABASES["default"]["NAME"]
        if arquivo.exists():
            if not recriar:
                self.stdout.write(f"O banco de demonstração já existe ({arquivo.name}). Nada a fazer.")
                return
            connection.close()
            arquivo.unlink()

        with connection.schema_editor() as editor:
            for model in MODELS:
                editor.create_model(model)
        with connection.cursor() as cursor:
            for comando in UNICIDADE:
                cursor.execute(comando)

        call_command("loaddata", "dados_exemplo", verbosity=0)
        self.stdout.write(self.style.SUCCESS(
            f"Banco de demonstração criado ({arquivo.name}). Entre com marina@email.com e a senha demonstracao."
        ))
