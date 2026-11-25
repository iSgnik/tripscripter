# Sprint 01 — Formulação algorítmica do problema

## Período

Início: [informar] · Fim: [informar]

## Objetivo

Identificar o problema que o TripScripter resolve, formulá-lo computacionalmente e demonstrar a viabilidade de uma solução algorítmica de recomendação.

## Milestone

Não aplicável. As milestones do repositório correspondem ao roadmap de desenvolvimento do MVP, definido posteriormente no Documento de Arquitetura. Esta Sprint antecede aquele roadmap.

## Itens planejados

- Identificação do problema com solução algorítmica
- Modelagem algorítmica: entrada, processamento e saída
- Definição da estrutura de dados
- Implementação do algoritmo de recomendação
- Levantamento das dimensões quantitativas do problema
- Definição do ambiente de programação
- Quadro-resumo do modelo de negócio (Canvas do MVP)

## Responsáveis

Trabalho conduzido pelos quatro integrantes: Diogo Heberth de Sousa Silva, Fernando Machado de Faria, Matheus Sousa Costa e Victor Hugo Américo Dos Santos Garajau.

## Entregas

Relatório *Sistema Algorítmico de Recomendação de Lugares Autênticos*, contendo:

- **Problema identificado:** turistas gastam tempo excessivo procurando lugares autênticos, porque buscadores exibem resultados patrocinados, avaliações são frequentemente manipuladas, não existe filtro por autenticidade e o usuário precisa analisar manualmente muitos resultados.
- **Formulação computacional:** dado um conjunto de locais cadastrados, um conjunto de filtros escolhidos pelo usuário e um limite de resultados, retornar os três locais mais relevantes. Caracteriza-se como problema de filtragem e ranqueamento por critérios múltiplos.
- **Estrutura de dados:** cada local representado como dicionário com nome, lista de tags, nota de autenticidade e preço médio; a base é uma lista desses dicionários.
- **Algoritmo:** função `recomendar_locais` em Python, que pontua cada local por compatibilidade de tags e por nota de autenticidade, ordena por pontuação e retorna os três primeiros.
- **Análise de complexidade:** O(N × T), onde N é o número de locais e T o número de tags selecionadas. Para N = 500 e T = 4, são 2.000 comparações por busca.
- **Métricas de validação definidas:** tempo médio de resposta abaixo de 1 segundo; redução do tempo de decisão de 30 a 60 minutos para cerca de 2 minutos; CTR de 40%; taxa de retorno de 25%; precisão média da recomendação igual ou superior a 4 em escala de 1 a 5.

## Issues concluídas

Não aplicável. O repositório institucional passou a ser utilizado pela equipe apenas na Sprint 5.

## Pull requests aceitos

Não aplicável, pelo mesmo motivo.

## Evidências

- Relatório da Sprint 1 em PDF, entregue à disciplina
- Código-fonte 1 (estrutura de dados) e Código-fonte 2 (algoritmo de recomendação), reproduzidos no relatório
- Apêndice A — Quadro-resumo do modelo de negócio (Canvas do MVP)

## Impedimentos

O ambiente de programação foi definido em duas alternativas — uma para o MVP, com ferramentas no-code, e outra para versão escalável, com Python e Flask. Essa indefinição foi resolvida apenas em Sprints posteriores, quando a arquitetura foi formalizada.

## Retrospectiva

A formulação computacional do problema, com análise de complexidade e métricas quantitativas de validação, deu à equipe uma base objetiva para discutir escopo nas Sprints seguintes.

Em contrapartida, a definição tecnológica ficou vaga: o relatório apresenta ferramentas no-code e um backend em Flask como caminhos possíveis, sem escolha. A ausência de decisão registrada nesta etapa gerou, nas Sprints seguintes, documentos que citavam tecnologias incompatíveis entre si.

## Próximas ações

- Formalizar a declaração de escopo do projeto
- Levantar e documentar os requisitos funcionais e não funcionais
- Converter o algoritmo de recomendação, concebido como produto autônomo, em módulo do TripScripter
