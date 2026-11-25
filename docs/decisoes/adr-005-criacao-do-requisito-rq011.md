# ADR 005 — Criação do requisito RQ011 para o histórico de viagens

## Título

Formalização do histórico de viagens como requisito, a partir de lacuna identificada entre os artefatos do projeto.

## Status

Aprovado.

## Data

2026-09-11

## Contexto

Durante a elaboração do backlog do produto, a equipe percorreu os artefatos existentes para garantir que cada história de usuário estivesse vinculada a um requisito formal.

A funcionalidade de consulta a viagens anteriores aparecia em três lugares: no escopo do produto, no diagrama de casos de uso e no roadmap de desenvolvimento. Não havia, porém, requisito correspondente no Documento de Requisitos.

A situação criava um problema de rastreabilidade: uma funcionalidade prevista para ser entregue não teria requisito que a justificasse nem critério que permitisse verificá-la.

## Decisão

Foi criado o requisito **RQ011 — Consulta ao histórico de viagens anteriores**, classificado como Desejável, e a ele foi vinculada a história B10 do backlog, estimada em 5 pontos e alocada na Sprint 6.

A lacuna foi registrada explicitamente no Documento de Arquitetura, na seção 3.5, e o requisito deve ser incorporado à próxima revisão do Documento de Requisitos.

## Alternativas consideradas

**Remover a funcionalidade do escopo e do diagrama de casos de uso.** Eliminaria a inconsistência pelo caminho oposto. Foi descartada porque a funcionalidade tem valor para o usuário e já constava do que havia sido apresentado.

**Tratar o histórico como parte do requisito de listagem de viagens.** Evitaria criar um requisito novo. Foi descartada porque a listagem trata de viagens em andamento e o histórico trata de viagens concluídas, com critérios de aceite distintos.

**Deixar a história no backlog sem requisito vinculado.** Foi descartada por quebrar a rastreabilidade entre requisito, história e Sprint, que é o que a disciplina cobra.

## Consequências

A rastreabilidade entre requisitos, histórias e Sprints fica completa: todas as dez histórias do backlog têm requisito de origem.

O Documento de Requisitos passa a estar desatualizado em relação ao Documento de Arquitetura até que a revisão seja feita, o que está registrado como pendência.

O episódio estabeleceu uma prática para a equipe: antes de fechar um artefato, conferir se cada item citado tem origem formal em outro documento do projeto.

## Links relacionados

- [Documento de Arquitetura de Software](../arquitetura.md), seção 3.5
- [Rastreabilidade de requisitos](../requisitos.md)
- Issue da história B10: #11
