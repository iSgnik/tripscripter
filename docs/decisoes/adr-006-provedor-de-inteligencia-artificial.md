# ADR 006 — Provedor de inteligência artificial

## Título

Groq como provedor principal de IA, Google Gemini como alternativa e cliente simulado como reserva.

## Status

Proposto.

## Data

2026-10-21

## Contexto

A geração automática de roteiro (RQ004) depende de um modelo de linguagem acessado por API. O projeto está sujeito a recursos financeiros escassos, com uso exclusivo de planos gratuitos, e o ADR 003 já determinou que o provedor fique isolado atrás da interface `ClienteIA`.

O sistema será usado em demonstrações ao professor, e não publicado. Isso traz dois requisitos práticos: nenhum integrante deve precisar cadastrar cartão de crédito, e a demonstração não pode depender inteiramente da rede da instituição nem de uma cota gratuita que pode se esgotar.

A redação original do RQ009 exigia a geração do roteiro em menos de 1 segundo, o que não é viável com chamada a um serviço externo de IA. O requisito foi reescrito na Sprint 5: até 1 segundo para consultar e editar o roteiro, e até 15 segundos para apresentar o roteiro gerado (ver [requisitos](../requisitos.md#sobre-o-rq009)).

Em outubro de 2026, os dois planos gratuitos avaliados que dispensam cartão tinham estas características, segundo levantamento publicado pelo OpenRouter (os limites mudam com frequência):

| | Groq | Google Gemini |
| --- | --- | --- |
| Limite | 30 requisições por minuto, 1.000 por dia | 5 a 15 por minuto, 20 a 1.500 por dia, conforme o modelo |
| Velocidade | Muito alta | Boa |
| Uso dos prompts para treino | Não | Sim, fora da União Europeia |

## Decisão

Foram implementados três adaptadores da interface `ClienteIA`, em `backend/integracao/ia/`:

- **`ClienteGroq`**, provedor principal, com o modelo `openai/gpt-oss-120b`;
- **`ClienteGemini`**, alternativa configurável, com o modelo `gemini-3.8-flash`;
- **`ClienteIASimulado`**, que monta o roteiro sem internet, a partir de um catálogo fixo.

O provedor é escolhido no arquivo `.env` (`IA_PROVEDOR`). Quando o provedor principal falha — sem rede, cota esgotada, chave ausente ou resposta ilegível —, o sistema usa o cliente simulado como reserva (`IA_RESERVA`) e informa o usuário de que o roteiro foi montado com sugestões pré-definidas.

A espera pela resposta do provedor é limitada a 12 segundos. Os 3 segundos restantes do limite do RQ009 cobrem a validação, a gravação e, se o provedor falhar, o uso da reserva.

Toda resposta da IA passa por validação campo a campo antes de ser gravada (`backend/dominio/roteirizacao.py`): coordenadas fora da faixa, custos negativos, horários inválidos, lugares repetidos e excesso de atividades são descartados.

## Alternativas consideradas

**Somente o Gemini.** Oferece janela de contexto maior, mas é mais lento, tem limites diários menores em alguns modelos e, fora da União Europeia, usa os prompts para treino no plano gratuito. Mantido como alternativa, não como principal.

**OpenRouter.** Dá acesso a vários modelos gratuitos com uma única chave, mas o limite gratuito é de 50 requisições por dia, baixo para o desenvolvimento e os testes.

**Modelo executado localmente.** Eliminaria a dependência de rede e de cota, mas exige computador com memória e processamento que nem todos os integrantes têm, e a geração ficaria lenta demais para a demonstração.

**Sem cliente de reserva.** Mais simples, mas faria a demonstração depender da rede e da cota no momento da apresentação.

## Consequências

A troca entre Groq e Gemini é uma alteração de uma linha no `.env`, sem mudança de código, como previsto no ADR 003.

Os testes automatizados não consomem cota: os adaptadores são testados com respostas falsas no formato de cada provedor, e a geração pela API é testada com o cliente simulado.

O modelo `llama-3.3-70b-versatile`, citado em levantamentos anteriores, foi desligado pelo Groq em 16 de agosto de 2026 para os planos gratuito e de desenvolvedor. Isso confirma o risco que motivou o ADR 003: os modelos e os limites dos provedores mudam sem controle da equipe. Por isso o modelo também é configurável no `.env`.

Pendências decorrentes desta decisão:

- incorporar a nova redação do RQ009 ao Documento de Requisitos;
- os adaptadores foram verificados com respostas simuladas; a primeira chamada real depende da criação das chaves de API.

A integração também mostrou que o front-end exibia a categoria de cada atividade sem que o banco tivesse onde guardá-la. A coluna `categoria` foi acrescentada à tabela `local`, e a IA passou a classificar cada lugar numa das oito categorias das preferências.

## Links relacionados

- [ADR 003 — Isolamento dos serviços externos](adr-003-isolamento-dos-servicos-externos.md)
- [Back-end — seção Inteligência artificial](../../backend/README.md)
- [Groq — modelos descontinuados](https://console.groq.com/docs/deprecations)
- [OpenRouter — comparação de planos gratuitos](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
