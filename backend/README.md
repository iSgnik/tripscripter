# Back-end

API REST do TripScripter, em Python com Django e Django REST Framework, sobre o banco PostgreSQL definido em [`banco/`](../banco/).

A organização das pastas segue o diagrama de pacotes (Figura 3 do [Documento de Arquitetura](../docs/arquitetura.md)):

| Pasta | Camada | Conteúdo |
| --- | --- | --- |
| `aplicacao/` | Aplicação | Views (Controllers), serializers (DTOs), services e rotas |
| `dominio/` | Domínio | Regras de negócio, sem dependência do Django |
| `persistencia/` | Persistência | Models do Django ORM, um por tabela do esquema |
| `integracao/` | Integração | Clientes de IA: Groq, Gemini e simulado (padrão Adapter, ADR 003). Mapas e clima ainda não |
| `comum/` | Comum | Autenticação, tratamento de erros e executor de testes |
| `config/` | — | Configuração do Django |

## O banco de dados é a fonte oficial da estrutura

O arquivo [`banco/01-esquema.sql`](../banco/01-esquema.sql) define as tabelas. Os models do Django apenas leem e gravam nelas: estão marcados com `managed = False`, e o projeto não tem migrations.

Na prática, isso significa que:

- **não se roda `python manage.py migrate`** — o banco é criado pelos scripts SQL;
- uma mudança de estrutura é feita primeiro no `01-esquema.sql` e depois refletida em `persistencia/models.py`;
- os testes automatizados criam um banco temporário a partir do mesmo `01-esquema.sql`, e por isso verificam as restrições reais do PostgreSQL.

O sistema de usuários padrão do Django não é usado, porque exigiria a tabela `auth_user`, que não existe no modelo físico aprovado. A autenticação usa a tabela `usuario` do esquema, com token assinado (ver `comum/seguranca.py`).

## Instalação

Requisitos: Python 3.12 ou superior e PostgreSQL 16.

```bash
# 1. Criar o banco e carregar a estrutura e os dados de exemplo
createdb tripscripter
psql -d tripscripter -f ../banco/01-esquema.sql
psql -d tripscripter -f ../banco/02-dados-exemplo.sql

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux ou macOS

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar o ambiente
copy .env.example .env          # Windows  (cp no Linux ou macOS)
# depois, abrir o .env e preencher a senha do PostgreSQL

# 5. Subir o servidor
python manage.py runserver
```

A API fica em `http://127.0.0.1:8000/api/`.

### Entrar com os usuários de exemplo

Os usuários de `02-dados-exemplo.sql` têm senhas fictícias. Para usá-los na demonstração:

```bash
python manage.py definir_senha marina@email.com uma-senha-qualquer
```

## Testes

```bash
python manage.py test
```

São 77 testes, cobrindo os requisitos RQ001 a RQ009 e RQ011, o isolamento entre usuários e a geração de roteiro. Os testes de desempenho (RQ009) estão em `aplicacao/testes/test_desempenho.py`. Nenhum teste chama a internet nem consome cota dos provedores de IA. O usuário do PostgreSQL configurado no `.env` precisa ter permissão para criar bancos, porque o Django cria e apaga um banco temporário a cada execução.

## Rotas

Todas as rotas, exceto as marcadas como públicas, exigem o cabeçalho `Authorization: Bearer <token>`, com o token devolvido pelo cadastro ou pelo login.

| Método | Rota | Função | Requisito |
| --- | --- | --- | --- |
| POST | `/api/auth/cadastro/` | Cria a conta e devolve o token (pública) | RQ001 |
| POST | `/api/auth/login/` | Confere e-mail e senha e devolve o token (pública) | RQ002 |
| GET | `/api/opcoes/` | Categorias e estilos aceitos (pública) | RQ003 |
| GET | `/api/usuario/` | Dados do usuário autenticado | — |
| GET, PUT | `/api/preferencias/` | Consulta ou substitui as preferências | RQ003, RQ004 |
| GET, POST | `/api/viagens/` | Lista as viagens atuais e futuras, ou cria uma | RQ003 |
| GET | `/api/viagens/historico/` | Viagens encerradas | RQ011 |
| GET, PATCH, DELETE | `/api/viagens/<id>/` | Roteiro completo, edição de destino e estilo, exclusão | RQ005, RQ006 |
| POST | `/api/viagens/<id>/gerar-roteiro/` | Preenche os dias com a sugestão da IA | RQ004 |
| POST | `/api/viagens/<id>/reaproveitar/` | Nova viagem com o mesmo roteiro, em outra data | RQ011 |
| POST | `/api/dias/<id>/atividades/` | Inclui atividade ao final do dia | RQ007 |
| POST | `/api/dias/<id>/reordenar/` | Grava a nova ordem das atividades | RQ007 |
| PATCH, DELETE | `/api/atividades/<id>/` | Edita horário e custo, ou remove | RQ007 |
| GET, POST | `/api/atividades/<id>/notas/` | Notas da atividade | RQ008 |
| PATCH, DELETE | `/api/notas/<id>/` | Edita ou apaga uma nota | RQ008 |

Toda resposta de erro tem o formato `{"erro": "mensagem", "detalhes": {...}}`.

### Exemplo: criar uma viagem

```http
POST /api/viagens/
Authorization: Bearer <token>
Content-Type: application/json

{
  "destino": "Lisboa, Portugal",
  "data_inicio": "2026-12-01",
  "data_fim": "2026-12-03",
  "estilo_viagem": "Equilibrado",
  "preferencias": [
    {"categoria": "Cultura", "nivel_interesse": 5},
    {"categoria": "Gastronomia", "nivel_interesse": 4}
  ]
}
```

A resposta traz a viagem com três dias de roteiro, ainda sem atividades. Para preenchê-los, chame `POST /api/viagens/<id>/gerar-roteiro/`.

## Inteligência artificial

A geração do roteiro (RQ004) é feita pelo `GeradorRoteiroService` (`aplicacao/gerador_roteiro.py`), o mesmo do diagrama de classes. A decisão sobre os provedores está no [ADR 006](../docs/decisoes/adr-006-provedor-de-inteligencia-artificial.md).

### Escolher o provedor

No `.env`:

| Variável | Valores | Padrão |
| --- | --- | --- |
| `IA_PROVEDOR` | `groq`, `gemini` ou `simulado` | `simulado` |
| `IA_RESERVA` | `simulado` ou `nenhuma` | `simulado` |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | chave do provedor | vazio |
| `GROQ_MODELO`, `GEMINI_MODELO` | nome do modelo | `openai/gpt-oss-120b`, `gemini-3.8-flash` |
| `IA_TEMPO_LIMITE` | segundos de espera pelo provedor | `12` |

Sem chave, o sistema funciona com o cliente simulado, que monta roteiros para Paris, Tóquio e Lisboa com locais reais e coordenadas, e sugestões genéricas para outros destinos.

**A chave de API nunca vai para o repositório.** Ela fica só no `.env`, que está no `.gitignore`. Quem tiver a chave publicada pode usar a cota de vocês, e os provedores costumam desativar chaves encontradas no GitHub.

### Como a geração funciona

1. O serviço reúne destino, datas, ritmo e preferências do usuário.
2. Pede a sugestão ao provedor configurado, esperando no máximo `IA_TEMPO_LIMITE` segundos (12, para caber nos 15 segundos do RQ009).
3. Se o provedor falhar, usa a reserva e devolve um aviso. Sem reserva, a API responde 503.
4. Valida a sugestão campo a campo (`dominio/roteirizacao.py`). Coordenadas inválidas, custos negativos, horários impossíveis, lugares repetidos e atividades em excesso são descartados. A categoria só é aceita se for uma das oito das preferências (Cultura, Gastronomia, Arte, Natureza, História, Compras, Vida noturna, Praia).
5. Grava tudo numa única transação, reaproveitando locais que já estejam no catálogo.

O número de atividades por dia depende do ritmo: 3 no Tranquilo, 4 no Equilibrado e 6 no Intenso.

Se o roteiro já tiver atividades, a geração exige `{"substituir": true}`, porque apaga as atividades e as notas atuais. Sem isso, a API responde 409.

A resposta informa quem gerou o roteiro e quanto tempo levou, o que permite conferir o RQ009 na demonstração:

```json
{
  "geracao": {"provedor": "Groq", "aviso": null, "tempo_em_ms": 2340, "total_de_atividades": 12},
  "viagem": { "...": "roteiro completo" }
}
```

## Regras de negócio

- Uma viagem tem no máximo 30 dias (`dominio/regras.py`).
- Ao criar a viagem, é gerado um dia de roteiro para cada data do período.
- Destino e estilo podem ser alterados depois; as datas, não. Mudar o período exigiria decidir o que fazer com as atividades dos dias que deixariam de existir.
- As preferências são do usuário, não da viagem, conforme o modelo físico. As escolhidas no assistente substituem as anteriores.
- Ao remover uma atividade, as restantes do dia são renumeradas.
- Um usuário que tente acessar a viagem de outro recebe 404, como se ela não existisse.
