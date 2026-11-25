"""
Define a senha de um usuário já cadastrado.

Os usuários de banco/02-dados-exemplo.sql têm resumos de senha fictícios e,
por isso, não conseguem entrar no sistema. Este comando grava um resumo real,
para que possam ser usados na demonstração:

    python manage.py definir_senha marina@email.com minha-senha
"""

from django.core.management.base import BaseCommand, CommandError

from persistencia.models import Usuario


class Command(BaseCommand):
    help = "Define a senha de um usuário existente (útil para os dados de exemplo)."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("senha")

    def handle(self, *args, email, senha, **opcoes):
        try:
            usuario = Usuario.objects.get(email=email.strip().lower())
        except Usuario.DoesNotExist:
            raise CommandError(f"Nenhum usuário com o e-mail {email}.")
        usuario.definir_senha(senha)
        usuario.save(update_fields=["senha_hash"])
        self.stdout.write(self.style.SUCCESS(f"Senha de {usuario.nome} atualizada."))
