# ADR 004 — Adiamento do aplicativo móvel nativo para o Projeto Integrador II

## Título

Limitação do produto mínimo viável à aplicação web, com acesso móvel por navegador.

## Status

Aprovado.

## Data

2026-08-27

## Contexto

A Declaração de Escopo prevê que o sistema seja usado em computador ou celular. Documentos anteriores do projeto chegaram a mencionar tecnologias de desenvolvimento móvel, como Flutter e React Native, sem que a decisão tivesse sido formalizada.

Uma versão anterior do Documento de Arquitetura atribuía a exclusão do aplicativo móvel à Declaração de Escopo, usando terminologia de priorização MoSCoW. Verificou-se que nem a exclusão nem essa terminologia constavam do documento referenciado. A atribuição era incorreta e precisava ser corrigida.

O cronograma é de seis Sprints de duas semanas, com uma equipe de quatro estudantes que também responde pela documentação acadêmica do projeto.

## Decisão

O produto mínimo viável é entregue como aplicação web. O acesso por dispositivos móveis ocorre pelo navegador, por meio de interface responsiva, o que atende ao previsto na Declaração de Escopo.

O aplicativo móvel nativo não integra o MVP e fica previsto para o Projeto Integrador II.

A decisão é assumida como escolha arquitetural da equipe, e não como restrição herdada de outro documento.

## Alternativas consideradas

**Desenvolver aplicativo nativo em paralelo à aplicação web.** Foi descartada por inviabilidade de cronograma: exigiria uma segunda base de código e uma segunda curva de aprendizado, com a mesma equipe e o mesmo prazo.

**Substituir a aplicação web pelo aplicativo móvel.** Foi descartada porque a avaliação acadêmica e a demonstração ocorrem em computador, e porque o planejamento de viagem é uma atividade frequentemente realizada em tela grande.

**Aplicativo híbrido empacotando a aplicação web.** Foi considerada para uma etapa posterior, mas descartada no MVP por não agregar capacidade além da que o navegador já oferece.

## Consequências

O escopo do semestre fica compatível com o cronograma e com o tamanho da equipe.

A construção do aplicativo no Projeto Integrador II não exigirá alteração no servidor: ele consumirá a mesma API REST, conforme estabelecido no ADR 001.

Recursos que dependem de capacidades nativas do aparelho, como uso de GPS em segundo plano ou funcionamento sem conexão, ficam fora do MVP.

## Links relacionados

- [Documento de Arquitetura de Software](../arquitetura.md), seções 1.2 e 2.5
- [ADR 001 — Arquitetura em camadas](adr-001-arquitetura-em-camadas.md)
