"""
Configuração do servidor do TripScripter.

Os valores que mudam de máquina para máquina (senha do banco, chave secreta)
são lidos do arquivo .env, que não vai para o repositório. O modelo desse
arquivo está em .env.example.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
RAIZ_DO_PROJETO = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "chave-apenas-para-desenvolvimento")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]


# -----------------------------------------------------------------------------
# Aplicações
#
# O django.contrib.auth não está instalado de propósito. O TripScripter usa a
# própria tabela usuario, definida em banco/01-esquema.sql, e não a tabela de
# usuários padrão do Django. Ver comum/seguranca.py.
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "persistencia",
    "aplicacao",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# -----------------------------------------------------------------------------
# Banco de dados
#
# A estrutura das tabelas vem de banco/01-esquema.sql, que é a fonte oficial
# do modelo. Os models do Django apenas leem e gravam nessas tabelas e não
# geram migrations (managed = False em persistencia/models.py).
# -----------------------------------------------------------------------------

DB_MOTOR = os.getenv("DB_MOTOR", "postgresql")

if DB_MOTOR == "sqlite":
    # Modo de demonstração: o banco é um único arquivo, sem instalar nada.
    # Serve para apresentar o sistema num computador sem PostgreSQL. Não
    # substitui o banco oficial: o SQLite não aplica as restrições CHECK do
    # 01-esquema.sql, e os testes automatizados rodam só no PostgreSQL.
    # O arquivo é criado com: python manage.py criar_banco_demo
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("DB_ARQUIVO", "demo.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NOME", "tripscripter"),
            "USER": os.getenv("DB_USUARIO", "postgres"),
            "PASSWORD": os.getenv("DB_SENHA", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORTA", "5432"),
        }
    }

ARQUIVO_ESQUEMA = RAIZ_DO_PROJETO / "banco" / "01-esquema.sql"

# Os testes automatizados criam um banco temporário e executam nele o
# 01-esquema.sql, em vez de migrations. Ver comum/testes.py.
TEST_RUNNER = "comum.testes.ExecutorDeTestesComEsquemaSQL"


# -----------------------------------------------------------------------------
# Senhas
#
# PBKDF2 é o algoritmo padrão do Django. O resumo gerado ocupa cerca de 90
# caracteres e cabe na coluna senha_hash, de 255.
# -----------------------------------------------------------------------------

PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]

# Validade do token de acesso devolvido no login, em segundos (7 dias).
VALIDADE_DO_TOKEN = 7 * 24 * 60 * 60


# -----------------------------------------------------------------------------
# API REST
# -----------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["comum.seguranca.AutenticacaoPorToken"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # Sem django.contrib.auth, o usuário não autenticado é representado por None.
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "comum.excecoes.tratar_excecao",
}

# Durante o desenvolvimento, o front-end é aberto direto do disco (file://)
# ou por um servidor local, e precisa de permissão para chamar a API.
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGENS", "").split(",") if o.strip()]


# -----------------------------------------------------------------------------
# Inteligência artificial (integracao/ia/, ADR 003)
#
# O padrão é o cliente simulado, que funciona sem chave e sem internet.
# Para usar um provedor real, defina IA_PROVEDOR e a chave correspondente no
# .env. As chaves nunca são escritas neste arquivo.
# -----------------------------------------------------------------------------

IA_PROVEDOR = os.getenv("IA_PROVEDOR", "simulado")
IA_RESERVA = os.getenv("IA_RESERVA", "simulado")

# Tempo máximo de espera pela resposta do provedor, em segundos. O RQ009
# admite até 15 segundos para apresentar o roteiro gerado; os 3 segundos
# restantes cobrem a validação, a gravação e, se o provedor falhar, o uso da
# reserva. Ver aplicacao/testes/test_desempenho.py.
IA_TEMPO_LIMITE = int(os.getenv("IA_TEMPO_LIMITE", "12"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODELO = os.getenv("GROQ_MODELO", "openai/gpt-oss-120b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELO = os.getenv("GEMINI_MODELO", "gemini-3.8-flash")


# -----------------------------------------------------------------------------
# Internacionalização
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = False  # as colunas do esquema são TIMESTAMP sem fuso horário

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
