# TripScripter — apresentação de 22/10

## Antes de sair de casa (5 minutos)

- [ ] Copie o `TripScripter_apresentacao.zip` para o **pendrive**.
- [ ] Mande o mesmo zip para o **seu e-mail ou Google Drive**, caso o pendrive falhe.
- [ ] Deixe a **chave do Groq** num lugar que você abra no PC da faculdade (uma nota no celular ou um e-mail para você). Ela **não** está no zip, de propósito.

## Na faculdade: preparação (cerca de 20 minutos, com folga)

### 1. Extrair (2 min)

Copie o zip para a Área de Trabalho, clique com o botão direito e escolha **Extrair tudo**. **Não rode nada de dentro do zip sem extrair**: o Windows não deixa criar arquivos ali.

### 2. Ligar (5 a 10 min)

Dê dois cliques em **`INICIAR_DEMONSTRACAO.bat`**, na pasta extraída.

- Se aparecer **"O Windows protegeu o computador"**, clique em **Mais informações** e depois em **Executar assim mesmo**.
- O script pede a chave do Groq. **Cole com o botão direito** (Ctrl+V nem sempre funciona nessa janela) e aperte Enter. Nada aparece enquanto você cola; é normal.
- Sem a chave, ou sem internet, apenas aperte Enter: o sistema usa o modo simulado.
- No fim, o navegador abre na tela de login e a janela preta mostra **"DEIXE ESTA JANELA ABERTA"**. Ela é o servidor: **não feche durante a apresentação**.

**Se o script disser que não encontrou o Python 3.12:**
1. Baixe em python.org/downloads (o botão amarelo).
2. Na primeira tela do instalador, marque **"Add python.exe to PATH"** e **desmarque** a opção de usar privilégios de administrador (*admin privileges*), se ela aparecer. Assim o Python é instalado só para o seu usuário, sem pedir senha.
3. Se mesmo assim pedir senha de administrador, peça ao técnico do laboratório, ou vá direto ao plano B.
4. Quando terminar, dê dois cliques no `.bat` outra vez.

### 3. Ensaiar uma vez (10 min)

Entre com **marina@email.com** e a senha **demonstracao**. Faça o roteiro abaixo uma vez, do começo ao fim.

Na tela de "Roteiro pronto", confira se aparece **"Gerado por Groq"**. Se aparecer "Simulado" com um aviso, a chave ou a internet não funcionaram. Dá para apresentar assim mesmo, e a reserva automática vira um ponto da apresentação (ver as perguntas no fim).

**Para recomeçar com os dados originais** depois do ensaio: feche a janela do servidor, apague o arquivo `backend\demo.sqlite3` e dê dois cliques no `.bat` de novo.

## Roteiro da demonstração (cerca de 10 minutos)

Cada passo responde a um item do feedback do professor.

| # | Tela | O que mostrar | Feedback / requisito |
| --- | --- | --- | --- |
| 1 | Login | A foto de fundo, como no protótipo | Item 3 (visual, cara de viagem) |
| 2 | Minhas viagens | Foto do destino nos cartões, etiquetas por categoria | Item 3 |
| 3 | Nova viagem | Os três passos; digite "Lisb" e mostre as sugestões; escolha interesses e ritmo; **Gerar roteiro** | RQ003, RQ004 (IA) |
| 4 | Roteiro pronto | "Gerado por Groq em X segundos" | RQ004 e RQ009 (tempo mensurável) |
| 5 | Roteiro | Adicione uma nota, mova uma atividade, inclua um local com horário (ele entra na posição certa), remova outro. **Aperte F5**: tudo continua lá | RQ005, RQ007, RQ008, banco de dados real |
| 6 | Mapa | Marcadores numerados com a cor da categoria; clique na lista e o mapa vai até o local | RQ006 |
| 7 | Histórico | Lisboa 2026; busque "cultura"; **Usar como modelo** cria a viagem nova com o mesmo roteiro | RQ011 |
| 8 | Perfil de viajante | Tela nova: interesses de 1 a 5 (os mesmos que a IA recebe) e locais visitados | Item 5 (páginas faltantes) |
| 9 | VS Code | A pasta `backend`: cada subpasta é um pacote da Figura 3 (`aplicacao`, `dominio`, `persistencia`, `integracao`, `comum`) | Item 1 (camadas e MVC) |
| 10 | VS Code | `backend/integracao/ia/`: um arquivo por provedor, atrás da interface `ClienteIA` | ADR 003 e ADR 006 |

## Perguntas prováveis

**"Por que não está usando o PostgreSQL aqui?"**
O banco oficial continua sendo o PostgreSQL 16, com o esquema em `banco/01-esquema.sql`, e os 78 testes automatizados rodam nele. Para apresentar num computador sem PostgreSQL, o back-end tem um modo de demonstração com SQLite, ligado por uma linha do `.env` (`DB_MOTOR`). As tabelas e os dados são os mesmos.

**"E se a IA cair durante a apresentação?"**
O sistema usa automaticamente um gerador de reserva, com sugestões pré-definidas, e avisa o usuário. Isso é o padrão Adapter do ADR 003: a troca de provedor não afeta o resto do sistema.

**"Qual modelo de IA vocês usam?"**
Groq, modelo `openai/gpt-oss-120b`, no plano gratuito, sem cartão. O Llama 3.3, citado antes, foi desligado pelo Groq em agosto, o que confirmou o risco previsto no ADR 003. O Gemini está implementado como alternativa. Tudo está no ADR 006.

**"Como vocês garantem que a resposta da IA não estraga o banco?"**
Toda resposta passa por validação campo a campo antes de ser gravada (`backend/dominio/roteirizacao.py`): coordenadas impossíveis, custos negativos, horários inválidos, lugares repetidos e atividades em excesso são descartados.

**"E o RQ009, de menos de 1 segundo?"**
Foi reescrito: até 1 segundo para consultar e editar o roteiro, e até 15 segundos para gerar com IA, porque a geração depende de um serviço externo. Há testes que medem os dois limites. A justificativa está em `docs/requisitos.md`.

**"Por que JavaScript puro, e não React como no protótipo?"**
ADR 002: ninguém da equipe programa em React, e aprender custaria pelo menos uma Sprint. O protótipo valida a interface; o código a implementa.

## Plano B

| Problema | O que fazer |
| --- | --- |
| Sem internet | Funciona no modo simulado. As fotos e o fundo do mapa não aparecem; o resto, sim. |
| Sem Python e sem como instalar | Mostre as capturas da pasta `telas`, o protótipo no Figma e o código no VS Code. |
| A tela mostra "Não foi possível falar com o servidor" | A janela preta foi fechada ou parou. Dê dois cliques no `.bat` de novo. |
| Esqueceu a senha | marina@email.com / demonstracao |

## Depois da apresentação

- **Não envie o `backend\.env` para o GitHub**: é ele que guarda a chave do Groq. O `.gitignore` já o exclui.
- Gere uma chave nova do Groq quando puder. A atual apareceu em capturas de tela.
