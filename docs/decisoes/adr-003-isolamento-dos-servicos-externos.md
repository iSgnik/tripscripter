# ADR 003 — Isolamento dos serviços externos pelo padrão Adapter

## Título

Encapsulamento dos provedores de inteligência artificial, mapas e previsão do tempo atrás de interfaces próprias.

## Status

Aprovado.

## Data

2026-08-27

## Contexto

O TripScripter depende de três serviços externos para funcionar: inteligência artificial, para sugerir a composição das atividades; mapas, para geolocalização e cálculo de distâncias; e previsão do tempo, para priorizar locais fechados em dias de chuva.

O projeto está sujeito a duas restrições diretamente relacionadas a essa dependência: recursos financeiros escassos, com uso exclusivo de ferramentas gratuitas ou de código aberto, e dependência dos planos gratuitos oferecidos pelos provedores.

A equipe registrou como risco a possibilidade de os custos das APIs de mapas ou de inteligência artificial excederem os limites gratuitos durante o desenvolvimento. Caso isso ocorra, será necessário trocar de provedor sem parar o projeto.

## Decisão

O consumo dos serviços externos é encapsulado em uma camada de integração, atrás das interfaces `ClienteIA`, `ClienteMapas` e `ClienteClima`, aplicando o padrão Adapter.

Nenhuma outra camada conhece o provedor concreto. A substituição de um provedor exige apenas uma nova implementação da interface correspondente.

## Alternativas consideradas

**Chamada direta às bibliotecas de cada provedor a partir da camada de aplicação.** Seria mais simples de escrever. Foi descartada porque espalharia o provedor por todo o código: uma troca obrigaria a alterar cada ponto de chamada, e o risco de estouro de plano gratuito é considerado provável.

**Escolha antecipada e definitiva de um provedor por serviço.** Evitaria a camada de indireção. Foi descartada porque a equipe não tem, no momento da decisão, informação suficiente sobre consumo real para escolher com segurança.

## Consequências

A troca de provedor — por exemplo, a migração do serviço de mapas do Google Maps para o OpenStreetMap — passa a ser uma alteração localizada, sem impacto nas camadas de domínio, aplicação ou apresentação.

O custo é a escrita de uma camada adicional de código que, enquanto o provedor não mudar, não produz benefício visível.

As interfaces também facilitam os testes: implementações de teste podem substituir os provedores reais, evitando consumo de cota durante o desenvolvimento.

## Links relacionados

- [Documento de Arquitetura de Software](../arquitetura.md), seções 2.2 e 2.5
- [ADR 001 — Arquitetura em camadas](adr-001-arquitetura-em-camadas.md)
