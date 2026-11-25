# Banco de dados

Scripts SQL do banco de dados do TripScripter, implementando o modelo físico apresentado na Figura 5 do [Documento de Arquitetura de Software](../docs/arquitetura.md), seção 5.2.

O banco não está integrado à aplicação web nesta entrega. O front-end opera sobre dados em memória, conforme registrado nas limitações do projeto. A integração está prevista para a Sprint 2 do roadmap, com a construção da API REST.

## Sistema gerenciador

PostgreSQL 16. Os scripts usam recursos específicos desse sistema: o tipo `SERIAL` para chaves primárias, `TRUNCATE ... RESTART IDENTITY` e blocos `DO $$ ... $$` em PL/pgSQL.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| [01-esquema.sql](01-esquema.sql) | Criação das sete tabelas, com chaves, restrições, comentários e índices |
| [02-dados-exemplo.sql](02-dados-exemplo.sql) | Carga de dados que permite demonstrar todos os requisitos |
| [03-consultas.sql](03-consultas.sql) | Doze consultas, cada uma vinculada a um requisito e a uma tela |
| [04-testes-integridade.sql](04-testes-integridade.sql) | Dez testes que verificam se as restrições rejeitam dados inválidos |

Os scripts devem ser executados nessa ordem. O primeiro apaga as tabelas antes de criá-las, e o segundo esvazia os dados antes de carregá-los, de modo que a sequência pode ser repetida quantas vezes for necessário.

## Execução

Criar o banco e rodar os quatro scripts:

```bash
createdb tripscripter
psql -d tripscripter -f 01-esquema.sql
psql -d tripscripter -f 02-dados-exemplo.sql
psql -d tripscripter -f 03-consultas.sql
psql -d tripscripter -f 04-testes-integridade.sql
```

Dependendo da instalação, pode ser necessário informar o usuário com `-U`.

## Estrutura

Sete tabelas, conforme o Quadro 7 do Documento de Arquitetura:

| Tabela | Finalidade | Requisito |
| --- | --- | --- |
| `usuario` | Dados de cadastro e credenciais de acesso | RQ001, RQ002 |
| `preferencia` | Categorias de interesse do usuário e o nível de cada uma | RQ003, RQ004 |
| `viagem` | Destino, período e estilo de cada viagem planejada | RQ003 |
| `dia_roteiro` | Cada dia da viagem e sua ordem dentro do roteiro | RQ005 |
| `atividade_roteiro` | Atividade sugerida para um dia, com horário, ordem e custo | RQ005, RQ007 |
| `local` | Catálogo de pontos turísticos, com endereço, coordenadas e categoria | RQ006 |
| `nota_pessoal` | Anotações privadas do usuário sobre uma atividade | RQ008 |

A consulta ao histórico de viagens (RQ011) não exige tabela própria: é obtida filtrando em `viagem` os registros cuja data de término já passou.

## Decisões de modelagem

**`dia_roteiro` como entidade própria.** É ela que permite registrar a que dia cada atividade pertence. Sem essa entidade intermediária, não haveria onde organizar o roteiro por dias, que é o que o RQ005 exige.

**`local` separado de `atividade_roteiro`.** O mesmo ponto turístico pode ser sugerido em viagens diferentes, de usuários diferentes. Manter o local como entidade própria evita duplicar endereço e coordenadas a cada roteiro gerado. A consulta 12 demonstra esse reaproveitamento.

**Categoria no `local`, e não na atividade.** A categoria (Cultura, Gastronomia, Arte, Natureza, História, Compras, Vida noturna, Praia) é uma característica do lugar: um museu é Cultura em qualquer roteiro em que apareça. Usa a mesma classificação de `preferencia`, o que permite comparar o roteiro gerado com os interesses do usuário. A coluna aceita nulo, porque um local incluído à mão pode não ter categoria informada. Foi acrescentada na Sprint 5, quando a integração com a API mostrou que a interface exibia a categoria de cada atividade sem que o banco tivesse onde guardá-la.

**`preferencia` normalizada.** Cada preferência é um par formado por categoria e nível de interesse, em vez de uma coluna booleana por categoria. Assim, incluir uma nova categoria de atividade não exige alterar a estrutura do banco.

**Senhas armazenadas como resumo criptográfico.** A coluna `senha_hash` guarda o resultado de uma função de hash, nunca a senha em texto puro. A comparação ocorre na aplicação.

**Exclusão em cascata nos dados do usuário, restrita no catálogo.** Apagar uma viagem remove seus dias, atividades e notas, porque esses registros não existem fora dela. Já o catálogo de locais é protegido: um local em uso por algum roteiro não pode ser apagado.

## Verificação

Os quatro scripts foram executados em PostgreSQL 16, na ordem indicada, a partir de um banco vazio. Os dez testes de integridade passaram, confirmando que as restrições declaradas rejeitam:

- e-mail repetido entre usuários
- categoria de preferência repetida para o mesmo usuário
- duas atividades na mesma posição de um dia
- viagem cuja data de término antecede a de início
- nível de interesse fora da escala de 1 a 5
- coordenada geográfica fora da faixa válida
- custo estimado negativo
- e-mail sem formato válido
- viagem vinculada a usuário inexistente
- exclusão de local em uso por um roteiro

O teste de exclusão em cascata confirmou que apagar uma viagem com 3 dias, 9 atividades e 3 notas remove todos esses registros, sem deixar órfãos.
