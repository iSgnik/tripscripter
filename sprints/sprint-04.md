# Sprint 04 — Arquitetura de software, front-end e DevOps

## Período

Início: [informar] · Fim: [informar]

## Objetivo

Formalizar a arquitetura de software do sistema e documentar, em anexos próprios, o front-end web e as práticas de DevOps adotadas pela equipe.

## Milestone

Não aplicável. Ver observação na [Sprint 01](sprint-01.md).

## Itens planejados

- Documento de Arquitetura de Software
- Anexo I — Front-end web
- Anexo II — DevOps

## Responsáveis

| Frente | Responsável |
| --- | --- |
| Documentação, front-end e modelagem de arquitetura | Matheus Sousa Costa |
| Facilitação e acompanhamento do processo | Victor Hugo Américo Dos Santos Garajau |
| Desenvolvimento | Diogo Heberth de Sousa Silva e Fernando Machado de Faria |

## Entregas

**Documento de Arquitetura de Software (versão 2.2)**, definindo o padrão arquitetural, a metodologia de desenvolvimento, o roadmap em Sprints, a modelagem UML e os modelos de dados.

**Anexo I — Front-end (versão 2.0)**, que passou a documentar a aplicação web efetivamente desenvolvida, e não mais um protótipo visual e uma arquitetura-alvo. Registra a organização interna do código, a navegação, a gestão de estado, a rastreabilidade entre funcionalidades e requisitos, o mapa interativo com Leaflet e OpenStreetMap, o design system com seus tokens e tipografia, e o tour visual das telas.

O anexo registra ainda, de forma explícita, as limitações da versão: dados em memória sem persistência, autenticação simulada sem verificação em servidor, ausência da geração de roteiro por inteligência artificial, geocodificação estática a partir de dicionário local, layout otimizado para telas largas e acessibilidade parcial. Apresenta também um plano de evolução em cinco ciclos.

**Anexo II — DevOps**, registrando as ferramentas e práticas adotadas: controle de versão com Git e GitHub, organização de tarefas com Trello, comunicação por Discord e prototipação no Figma, além das ferramentas previstas para uso futuro.

## Issues concluídas

Não aplicável. O repositório institucional passou a ser utilizado pela equipe apenas na Sprint 5.

## Pull requests aceitos

Não aplicável.

## Evidências

- Documento de Arquitetura de Software v2.2, em PDF
- Anexo I — Front-end v2.0, em PDF, com doze figuras das telas
- Anexo II — DevOps, em PDF
- Quadro do Trello com o registro das entregas realizadas

## Impedimentos

O Anexo I descreve oito telas da aplicação, incluindo mapa, modais de atividade e anotação, e perfil do viajante com abas de locais visitados e lista de desejos. Nem todas essas telas correspondem a código versionado e disponível à equipe, o que criou uma diferença entre o que a documentação descreve e o que pode ser demonstrado.

O Anexo I também referencia FastAPI como tecnologia do servidor, enquanto o Documento de Arquitetura passou a adotar Django e Django REST Framework. A divergência permaneceu aberta ao fim desta Sprint.

## Retrospectiva

O ponto mais forte foi o registro honesto das limitações no Anexo I. Declarar que a autenticação é simulada, que os dados não persistem e que a geração por inteligência artificial ainda não existe evita que a documentação prometa mais do que o produto entrega — postura que o próprio anexo nomeia como transparência acadêmica.

A fragilidade foi de sincronização: três documentos produzidos em paralelo acabaram citando tecnologias diferentes para a mesma camada. Faltou uma revisão cruzada antes da entrega.

## Próximas ações

- Responder ao ciclo de feedback do professor
- Unificar as referências tecnológicas entre os documentos
- Reconstruir o backlog do produto com rastreabilidade a requisitos
- Organizar o repositório institucional no GitHub
