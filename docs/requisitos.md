# Requisitos

Este documento reúne os requisitos do TripScripter e registra a rastreabilidade entre cada requisito, a história de usuário que o implementa, a issue correspondente no repositório e a Sprint de entrega.

As descrições dos requisitos RQ001 a RQ010 reproduzem o Documento de Requisitos elaborado na Sprint 2. O RQ011 foi criado posteriormente e ainda deve ser incorporado àquele documento.

## Requisitos funcionais

| Código | Requisito | Descrição | Prioridade | História | Issue | Sprint |
| --- | --- | --- | --- | --- | --- | --- |
| RQ001 | Cadastro de usuário | O sistema deverá permitir que o usuário crie uma conta informando dados básicos como nome, e-mail e senha. | Essencial | B01 | #2 | 1 |
| RQ002 | Login no sistema | O sistema deverá permitir que usuários autenticados realizem login utilizando e-mail e senha. | Essencial | B02 | #3 | 1 |
| RQ003 | Criação de viagem | O sistema deverá permitir que o usuário crie uma nova viagem informando destino, duração da viagem e preferências de atividades. | Essencial | B03, B04 | #4, #5 | 1 e 2 |
| RQ004 | Geração automática de roteiro | O sistema deverá gerar automaticamente um roteiro de viagem com base nas preferências informadas pelo usuário. | Essencial | B05 | #6 | 3 |
| RQ005 | Organização do roteiro | O sistema deverá organizar as atividades sugeridas em uma lista estruturada por dias. | Essencial | B06 | #7 | 4 |
| RQ006 | Visualização em mapa | O sistema deverá permitir que o usuário visualize os locais sugeridos em um mapa. | Importante | B07 | #8 | 5 |
| RQ007 | Edição do roteiro | O usuário deverá poder modificar o roteiro gerado, alterando a ordem das atividades, removendo sugestões e adicionando novos locais. | Importante | B08 | #9 | 5 |
| RQ008 | Notas pessoais | O sistema deverá permitir que o usuário adicione notas pessoais às atividades do roteiro. | Desejável | B09 | #10 | 6 |
| RQ011 | Histórico de viagens | O sistema deverá permitir que o usuário consulte suas viagens anteriores e reaproveite roteiros já criados. | Desejável | B10 | #11 | 6 |

## Requisitos não funcionais

| Código | Requisito | Descrição | Prioridade | Tratamento |
| --- | --- | --- | --- | --- |
| RQ009 | Desempenho | O sistema deverá responder às consultas e às operações de edição do roteiro em menos de 1 segundo e apresentar o roteiro gerado automaticamente em até 15 segundos após o envio das preferências, considerando o tempo de resposta do serviço externo de inteligência artificial. | Importante | Critério da Definição de Pronto |
| RQ010 | Usabilidade | A interface deverá ser simples e intuitiva, permitindo que usuários iniciantes consigam planejar uma viagem facilmente. | Importante | Critério da Definição de Pronto |

Por serem transversais a todas as histórias, RQ009 e RQ010 não figuram como itens isolados do backlog. São verificados a cada entrega, de modo que nenhuma funcionalidade é considerada concluída sem atender aos padrões de tempo de resposta e de facilidade de uso estabelecidos.

## Sobre o RQ011

O requisito RQ011 foi criado durante a elaboração do backlog do produto, na Sprint 5. A funcionalidade de consulta a viagens anteriores constava do escopo do produto, do diagrama de casos de uso e do roadmap de desenvolvimento, mas não havia sido formalizada como requisito no Documento de Requisitos.

A decisão de criá-lo, com as alternativas consideradas, está registrada no [ADR 005](decisoes/adr-005-criacao-do-requisito-rq011.md). O requisito deve ser incorporado à próxima revisão do Documento de Requisitos.

## Sobre o RQ009

A redação original exigia que o roteiro fosse gerado em menos de 1 segundo após o envio das preferências. O limite é inviável: a geração depende de um serviço externo de inteligência artificial, cujo tempo de resposta está fora do controle da aplicação e costuma ser de alguns segundos.

A nova redação, adotada na Sprint 5, separa dois tempos:

- **até 1 segundo** para o que o sistema faz sozinho, sem depender de serviço externo: consultar o roteiro e editá-lo;
- **até 15 segundos** para apresentar o roteiro gerado pela IA.

Os dois limites são verificáveis. Os testes automatizados em `backend/aplicacao/testes/test_desempenho.py` medem a consulta e a reordenação no pior caso permitido (30 dias com 6 atividades cada) e conferem que a espera máxima pelo provedor (12 segundos) deixa folga para o restante do processamento. Na demonstração, a resposta da geração informa o tempo gasto, em milissegundos.

Uma proposta anterior, de agosto de 2026, previa também o retorno de uma lista ranqueada de locais em menos de 1 segundo. Ela não foi adotada porque o módulo de ranqueamento descrito na Sprint 1 não foi implementado, e o requisito não deve citar funcionalidade inexistente.

A nova redação ainda deve ser incorporada ao Documento de Requisitos, junto com o RQ011.

## Classificação de prioridade

| Prioridade | Significado |
| --- | --- |
| Essencial | Funcionalidade sem a qual o sistema não cumpre seu propósito |
| Importante | Funcionalidade que agrega valor significativo, mas cuja ausência não inviabiliza o uso |
| Desejável | Funcionalidade complementar |

## Documentos relacionados

- [Documento de Arquitetura de Software](arquitetura.md) — a seção 3.5 traz o backlog priorizado completo, com as estimativas em pontos
- [Registros de decisão](decisoes/README.md)
- Backlog registrado como issues #2 a #11, com labels de requisito e prioridade e milestones por Sprint
