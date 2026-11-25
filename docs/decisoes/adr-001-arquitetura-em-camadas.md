# ADR 001 — Arquitetura em camadas sobre o estilo cliente-servidor

## Título

Adoção da arquitetura em camadas, organizada no estilo cliente-servidor, com comunicação por API REST.

## Status

Aprovado.

## Data

2026-08-27

## Contexto

O TripScripter precisa entregar, no mesmo produto, uma interface de uso no navegador, regras de negócio de montagem de roteiro e a integração com três serviços externos: inteligência artificial, mapas e previsão do tempo.

Duas restrições pesaram sobre a escolha. A primeira é a dependência de terceiros: os provedores externos podem mudar de preço, de contrato de API ou de disponibilidade ao longo do projeto. A segunda é o escopo declarado de evolução: um aplicativo móvel está previsto para etapa posterior e precisará consumir as mesmas regras de negócio, sem reimplementá-las.

Era necessário, portanto, definir uma organização que isolasse as regras de negócio tanto da interface quanto dos provedores externos.

## Decisão

O sistema é organizado em cinco camadas lógicas — apresentação, aplicação, domínio, persistência e integração — executadas no estilo cliente-servidor. O cliente roda no navegador e o servidor expõe uma API REST sobre HTTPS, com JSON como formato de troca.

A regra de dependência é unidirecional: as camadas mais externas dependem das mais internas, nunca o contrário. A camada de domínio não conhece framework, banco de dados nem provedor externo.

O cliente nunca acessa o banco de dados diretamente. Toda informação trafega pela API REST.

## Alternativas consideradas

**Aplicação monolítica com renderização no servidor.** Seria mais rápida de construir, já que o Django entrega templates prontos. Foi descartada porque o aplicativo móvel previsto para a etapa seguinte não teria como consumir as regras de negócio: seria preciso duplicá-las ou reescrever o servidor.

**Arquitetura de microsserviços.** Ofereceria isolamento ainda maior entre as partes. Foi descartada pelo custo operacional — múltiplos processos, orquestração e observabilidade — incompatível com uma equipe de quatro estudantes e com a restrição de uso exclusivo de ferramentas gratuitas.

**Acesso direto do cliente aos serviços externos.** Eliminaria uma camada intermediária. Foi descartada porque exporia as chaves de API no navegador e impediria o controle centralizado de consumo dos planos gratuitos.

## Consequências

A camada de domínio torna-se a parte mais estável e mais facilmente testável do sistema, por não depender de tecnologia externa.

O aplicativo móvel do Projeto Integrador II poderá ser construído sobre a mesma API REST, sem alteração no servidor.

Em contrapartida, há custo de indireção: uma funcionalidade simples atravessa mais camadas do que atravessaria em um monolito, e a equipe precisa manter a disciplina da regra de dependência para que o benefício se sustente.

## Links relacionados

- [Documento de Arquitetura de Software](../arquitetura.md), seções 2.1 e 2.5
- [ADR 002 — Front-end sem framework](adr-002-frontend-sem-framework.md)
- [ADR 004 — Adiamento do aplicativo móvel](adr-004-adiamento-do-aplicativo-movel.md)
