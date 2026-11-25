# Sprint 05 — Ciclo de feedback e organização do repositório

## Período

Início: [informar] · Fim: 2026-09-30

## Objetivo

Atender às correções apontadas pelo professor no ciclo de feedback, reconstruir o backlog com rastreabilidade completa e organizar o repositório institucional no GitHub.

## Milestone

Não aplicável. Ver observação na [Sprint 01](sprint-01.md).

## Itens planejados

- Correções no Documento de Arquitetura
- Reconstrução do backlog do produto
- Ajustes no protótipo e no front-end
- Organização do repositório institucional

## Responsáveis

| Frente | Responsável |
| --- | --- |
| Documentação, front-end, arquitetura e organização do repositório | Matheus Sousa Costa |
| Revisão de pull requests | Fernando Machado de Faria |
| Facilitação e acompanhamento | Victor Hugo Américo Dos Santos Garajau |
| Desenvolvimento | Diogo Heberth de Sousa Silva |

## Entregas

**Documento de Arquitetura (versão 3), reconstruído.** O arquivo editável original não estava disponível com nenhum integrante, e o documento foi remontado a partir do PDF entregue. Cresceu de 17 para 19 páginas e passou a incluir:

- seção explicando que a arquitetura em camadas e o padrão MVC são decisões em níveis de abstração distintos, e não sobreposição;
- correção das referências a React e a aplicação de página única, alinhando o documento à implementação em HTML, CSS e JavaScript;
- quadro de tecnologias com as versões efetivamente instaladas;
- substituição da priorização MoSCoW pela escala Essencial, Importante e Desejável, unificando a nomenclatura com a Declaração de Escopo;
- correção da afirmação sobre o escopo móvel, que atribuía indevidamente à Declaração de Escopo uma exclusão que ela não continha;
- redesenho do diagrama de pacotes.

**Backlog do produto reconstruído.** Dez histórias de usuário no formato "Eu como…", cada uma vinculada ao requisito que a originou, estimadas em pontos pela sequência de Fibonacci e alocadas às Sprints do roadmap. Total de 59 pontos, com velocidade média aproximada de 10 pontos por Sprint.

**Requisito RQ011 criado.** A consulta ao histórico de viagens aparecia no escopo, no diagrama de casos de uso e no roadmap, mas não tinha requisito formal. A lacuna foi identificada durante a elaboração do backlog e registrada no documento.

**Requisitos não funcionais reposicionados.** RQ009 e RQ010, por serem transversais a todas as histórias, saíram do backlog e passaram a integrar a Definição de Pronto.

**Front-end publicado e corrigido.** As páginas passaram a ser versionadas no repositório. A tela de criação de viagem foi reconstruída como assistente de três passos, alinhada ao protótipo. Três defeitos de navegação foram corrigidos: o botão "Nova viagem" apontava para âncora vazia, os dois botões "Ver roteiro" abriam a mesma viagem independentemente do cartão escolhido, e o roteiro renderizava sempre o mesmo destino, ignorando o parâmetro da URL.

**Repositório institucional organizado.** README preenchido, backlog registrado como issues com labels de requisito e de prioridade, milestones por Sprint do roadmap, documentação publicada em `docs/` e decisões registradas em `docs/decisoes/`.

## Issues concluídas

| Issue | Título |
| --- | --- |
| #13 | Publicar front-end do TripScripter no repositório |

As issues #2 a #11 correspondem às histórias do backlog e permanecem abertas, por representarem funcionalidades a desenvolver nas Sprints do roadmap.

## Pull requests aceitos

| PR | Conteúdo |
| --- | --- |
| #1 | Preenchimento do README com identificação, equipe e visão geral |
| #12 | Documento de Arquitetura em Markdown, figuras, PDF e rastreabilidade de requisitos |
| #14 | Front-end: páginas, folha de estilo e scripts |

## Evidências

- Documento de Arquitetura v3, publicado em `docs/arquitetura.md` e `docs/arquitetura.pdf`
- Rastreabilidade entre requisitos, histórias, issues e Sprints, em `docs/requisitos.md`
- Cinco registros de decisão em `docs/decisoes/`
- Issues #2 a #11, com labels de requisito e prioridade e milestones por Sprint
- Pull requests #1, #12 e #14, com descrição, validação e evidências

## Impedimentos

**Criação do GitHub Project bloqueada.** A organização CAMPUSCEUB restringe a criação de Projects a administradores, e o seletor de Project nas issues não aceita Projects de conta pessoal. O backlog está registrado como issues com labels e milestones, mas o quadro previsto na estrutura do repositório depende de ação do professor. Registrado como pendência.

**Identificação do repositório incompleta.** O DRT do professor e o IDProjeto no Portfólio de Projetos de TI do CEUB não foram localizados pela equipe e aguardam confirmação.

**Perda de arquivos do front-end.** Parte do trabalho de front-end produzido no ciclo anterior não havia sido versionada e não pôde ser recuperada: as telas de cadastro, mapa e histórico não integram esta entrega.

**Rastreabilidade inicial sem issues.** Os dois primeiros pull requests foram abertos antes de existirem issues correspondentes. A falha foi identificada e corrigida durante a Sprint.

## Retrospectiva

O ciclo de feedback foi produtivo porque as correções não se limitaram ao que foi apontado. A revisão cruzada dos artefatos revelou problemas que ninguém havia sinalizado — a lacuna do RQ011, a atribuição incorreta sobre o escopo móvel, a convivência de duas escalas de priorização.

A perda dos arquivos de front-end é o aprendizado mais caro da Sprint, e tem causa direta: o trabalho ficou em máquinas individuais, sem versionamento. É exatamente o que o repositório institucional existe para evitar.

A colaboração melhorou ao fim da Sprint, com o primeiro pull request revisado por outro integrante. Até então, as entregas vinham sendo mescladas pelo próprio autor, o que não produz o histórico de revisão que a disciplina espera.

## Próximas ações

- Obter do professor o DRT e o IDProjeto, e completar a identificação do README
- Solicitar a criação do GitHub Project na organização, ou permissão para criá-lo
- Reconstruir as telas de cadastro, mapa e histórico
- Transcrever as descrições completas dos requisitos para `docs/requisitos.md`
- Incorporar o RQ011 à próxima revisão do Documento de Requisitos
- Alinhar o Anexo I — Front-end à tecnologia de servidor adotada no Documento de Arquitetura
- Distribuir as issues entre os integrantes, de modo que a participação individual fique rastreável
