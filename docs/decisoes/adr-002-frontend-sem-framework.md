# ADR 002 — Front-end em HTML, CSS e JavaScript, sem framework

## Título

Implementação do cliente em tecnologias web fundamentais, sem adoção de framework de interface.

## Status

Aprovado.

## Data

2026-08-27

## Contexto

A camada de apresentação precisava ser definida antes do início da implementação. A equipe é composta por quatro estudantes com experiência prévia limitada em frameworks de interface, e o cronograma está limitado ao calendário acadêmico, com seis Sprints de duas semanas.

Documentos anteriores do projeto mencionavam React em alguns trechos, sem que essa escolha tivesse sido efetivamente tomada ou justificada. A inconsistência precisava ser resolvida e registrada.

As telas previstas para o MVP — autenticação, cadastro de viagem, listagem de viagens e visualização do roteiro diário — não apresentam complexidade de estado compartilhado que exija gerenciamento sofisticado.

## Decisão

O cliente é implementado em HTML5, CSS3 e JavaScript (ES6+), sem framework.

A interface é construída de forma responsiva, adaptando-se a telas de computador e de dispositivos móveis, conforme previsto na Declaração de Escopo.

Todas as referências a React e a aplicações de página única presentes na documentação foram corrigidas para refletir a implementação efetiva.

## Alternativas consideradas

**React.** É a tecnologia mais mencionada no mercado e havia sido citada em documentos anteriores. Foi descartada porque a curva de aprendizado foi estimada em ao menos uma Sprint completa — um sexto do cronograma — para um ganho que as telas do MVP não justificam.

**Vue.** Apresenta curva de aprendizado menor que a do React. Foi descartada pelo mesmo motivo, em menor grau, somada à ausência de experiência prévia da equipe.

**Biblioteca de componentes sem framework completo.** Reduziria o trabalho de estilização. Foi descartada por introduzir dependência externa sem resolver o ponto central, que é o tempo de aprendizado.

## Consequências

A equipe escreve mais código de manipulação do DOM do que escreveria com um framework, e o controle de estado das telas é feito manualmente.

Em compensação, não há etapa de compilação, nem dependências a instalar, nem versões a manter: os arquivos abrem diretamente no navegador, o que simplifica a demonstração acadêmica e a avaliação pelo professor.

A adoção de um framework permanece possível em versões posteriores, sem impacto sobre o servidor, uma vez que a comunicação já ocorre por API REST.

O protótipo produzido em Figma Make utiliza React e TypeScript. Trata-se de artefato de design, distinto da implementação, e a diferença de tecnologia entre os dois não constitui contradição.

## Links relacionados

- [Documento de Arquitetura de Software](../arquitetura.md), seções 2.4 e 2.5
- [ADR 001 — Arquitetura em camadas](adr-001-arquitetura-em-camadas.md)
- Pull request de publicação do front-end: #14
