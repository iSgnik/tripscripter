# Front-end

Telas do TripScripter em HTML, CSS e JavaScript, sem framework ([ADR 002](../docs/decisoes/adr-002-frontend-sem-framework.md)). O visual segue o protótipo do Figma Make; o código não reaproveita o do protótipo, que é React.

Todos os dados vêm da [API REST](../backend/README.md). Não há mais dados simulados nas telas.

## Como abrir

1. Suba o back-end, na pasta `backend/`:

   ```bash
   python manage.py runserver
   ```

2. Abra `frontend/index.html` no navegador, com duplo clique no arquivo.

As telas chamam a API em `http://127.0.0.1:8000/api`. Se o servidor não estiver rodando, cada tela mostra uma mensagem dizendo isso.

Para entrar com a usuária de exemplo, defina uma senha para ela antes, na pasta `backend/`:

```bash
python manage.py definir_senha marina@email.com uma-senha-qualquer
```

## Telas

| Arquivo | Tela | Requisito |
| --- | --- | --- |
| `index.html` | Login | RQ002 |
| `cadastro.html` | Criação de conta | RQ001 |
| `viagens.html` | Viagens planejadas | RQ003 |
| `nova-viagem.html` | Assistente em três passos e geração do roteiro | RQ003, RQ004 |
| `roteiro.html` | Roteiro por dia, com notas, reordenação, inclusão e remoção | RQ004, RQ005, RQ007, RQ008 |
| `mapa.html` | Roteiro em mapa | RQ006 |
| `historico.html` | Viagens concluídas e "usar como modelo" | RQ011 |
| `perfil.html` | Perfil de viajante: conta, interesses e locais visitados | RQ003, RQ004 |

As telas de roteiro e de mapa recebem a viagem pela URL: `roteiro.html?id=3`.

## Scripts

Toda página carrega, nesta ordem:

```html
<script src="js/comum.js"></script>   <!-- datas, fotos de destino, categorias -->
<script src="js/api.js"></script>     <!-- chamadas à API e sessão -->
<script src="js/<tela>.js"></script>  <!-- a lógica da própria tela -->
```

A ordem importa: `api.js` usa funções de `comum.js`, e o script da tela usa os dois.

## Sessão

O login devolve um token, guardado no navegador e enviado em toda chamada à API. Com "Manter conectado", ele sobrevive ao fechamento do navegador (`localStorage`); sem a opção, some ao fechar a aba (`sessionStorage`). O token expira em 7 dias; depois disso, a tela volta ao login.

## Serviços externos

Nenhum exige chave de API ou cadastro:

| Serviço | Uso | Sem internet |
| --- | --- | --- |
| Google Fonts | Bricolage Grotesque e Karla | Usa a fonte do sistema |
| Unsplash | Fotos de destino no login, no cadastro e nos cartões | Fica o degradê da paleta |
| CARTO / OpenStreetMap | Blocos do mapa | O mapa fica em branco, mas a lista de paradas funciona |
| Photon (OpenStreetMap) | Sugestões de destino no assistente | O campo aceita o texto digitado |

Só destinos com foto própria recebem imagem (Paris, Tóquio, Lisboa, Buenos Aires, Nova York e Barcelona, em `js/comum.js`). Os demais mantêm o degradê com o ícone, porque mostrar a foto de outra cidade seria enganoso.

A biblioteca Leaflet, que desenha o mapa, fica no próprio projeto, em `bibliotecas/leaflet/`, para não depender de um servidor externo.

## Convenções

- Nomes de classes e variáveis em português, no padrão do CSS original da equipe (`.painel`, `.barra`, `.viagem`, `.trilha`, `.parada`).
- O CSS cresce por seções numeradas ao fim do arquivo. As seções 1 a 11 são as originais; 12 a 20 foram acrescentadas com a integração à API e o alinhamento ao protótipo.
- Todo texto vindo da API passa por `Trip.escapar` antes de entrar no HTML, para que um nome de local com `<script>` apareça como texto, e não rode.
