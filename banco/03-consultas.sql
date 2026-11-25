-- =============================================================================
-- TripScripter — Consultas de demonstração
--
-- Cada consulta demonstra um requisito do sistema. O comentário acima de
-- cada uma indica qual requisito ela atende e qual tela da aplicação web
-- consumiria esse resultado.
--
-- Execução, após 01-esquema.sql e 02-dados-exemplo.sql:
--   psql -U <usuario> -d tripscripter -f 03-consultas.sql
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. RQ002 — Autenticação
--    Tela: index.html (acesso)
--
--    Recupera o resumo da senha para que a aplicação o compare com o que foi
--    digitado. A comparação ocorre na aplicação, nunca no banco, e a senha em
--    texto puro jamais trafega até aqui.
-- -----------------------------------------------------------------------------

SELECT id_usuario, nome, senha_hash
  FROM usuario
 WHERE email = 'marina@email.com';


-- -----------------------------------------------------------------------------
-- 2. RQ003 — Viagens do usuário
--    Tela: viagens.html (minhas viagens)
--
--    Lista as viagens em andamento ou futuras, com a duração calculada a
--    partir do período e a contagem de atividades já planejadas.
-- -----------------------------------------------------------------------------

SELECT v.id_viagem,
       v.destino,
       v.data_inicio,
       v.data_fim,
       (v.data_fim - v.data_inicio) + 1       AS dias,
       v.estilo_viagem,
       COUNT(a.id_atividade)                  AS atividades
  FROM viagem v
  LEFT JOIN dia_roteiro       d ON d.id_viagem = v.id_viagem
  LEFT JOIN atividade_roteiro a ON a.id_dia    = d.id_dia
 WHERE v.id_usuario = 1
   AND v.data_fim >= DATE '2026-05-01'
 GROUP BY v.id_viagem, v.destino, v.data_inicio, v.data_fim, v.estilo_viagem
 ORDER BY v.data_inicio;


-- -----------------------------------------------------------------------------
-- 3. RQ005 — Roteiro organizado por dia
--    Tela: roteiro.html (visão em lista)
--
--    Esta é a consulta central do sistema. Percorre as quatro tabelas que
--    formam o roteiro e devolve as atividades já na ordem em que devem ser
--    exibidas: por dia, e dentro do dia, pela posição definida.
-- -----------------------------------------------------------------------------

SELECT d.ordem                AS dia,
       d.data,
       a.ordem_do_dia         AS posicao,
       a.hora_sugerida,
       l.nome                 AS local,
       a.custo_estimado,
       n.texto                AS nota_pessoal
  FROM viagem v
  JOIN dia_roteiro        d ON d.id_viagem    = v.id_viagem
  JOIN atividade_roteiro  a ON a.id_dia       = d.id_dia
  JOIN local              l ON l.id_local     = a.id_local
  LEFT JOIN nota_pessoal  n ON n.id_atividade = a.id_atividade
 WHERE v.id_viagem = 1
 ORDER BY d.ordem, a.ordem_do_dia;


-- -----------------------------------------------------------------------------
-- 4. RQ006 — Locais de um dia, para a visualização em mapa
--    Tela: mapa.html
--
--    Devolve apenas as atividades cujo local já foi geocodificado. As demais
--    aparecem na lista lateral marcadas como "sem localização", de modo que
--    a ausência de coordenada não quebre o mapa.
-- -----------------------------------------------------------------------------

SELECT a.ordem_do_dia AS parada,
       l.nome,
       l.latitude,
       l.longitude,
       a.hora_sugerida
  FROM atividade_roteiro a
  JOIN local             l ON l.id_local = a.id_local
 WHERE a.id_dia = 1
   AND l.latitude IS NOT NULL
   AND l.longitude IS NOT NULL
 ORDER BY a.ordem_do_dia;


-- -----------------------------------------------------------------------------
-- 5. RQ004 — Preferências que orientam a geração do roteiro
--    Tela: nova-viagem.html (passo 2)
--
--    O serviço de inteligência artificial recebe estas categorias, ordenadas
--    pelo nível de interesse, para compor as sugestões.
-- -----------------------------------------------------------------------------

SELECT categoria, nivel_interesse
  FROM preferencia
 WHERE id_usuario = 1
 ORDER BY nivel_interesse DESC, categoria;


-- -----------------------------------------------------------------------------
-- 6. RQ011 — Histórico de viagens concluídas
--    Tela: historico.html
--
--    Considera concluída a viagem cuja data de término já passou. O resumo
--    exibido no topo da tela (viagens, destinos e dias) sai da consulta 7.
-- -----------------------------------------------------------------------------

SELECT v.destino,
       v.data_inicio,
       v.data_fim,
       (v.data_fim - v.data_inicio) + 1 AS dias,
       COUNT(a.id_atividade)            AS atividades_realizadas
  FROM viagem v
  LEFT JOIN dia_roteiro       d ON d.id_viagem = v.id_viagem
  LEFT JOIN atividade_roteiro a ON a.id_dia    = d.id_dia
 WHERE v.id_usuario = 1
   AND v.data_fim < DATE '2026-05-01'
 GROUP BY v.id_viagem, v.destino, v.data_inicio, v.data_fim
 ORDER BY v.data_fim DESC;


-- -----------------------------------------------------------------------------
-- 7. RQ011 — Resumo em números do histórico
--    Tela: historico.html (cartões do topo)
-- -----------------------------------------------------------------------------

SELECT COUNT(*)                                       AS viagens_concluidas,
       COUNT(DISTINCT v.destino)                      AS destinos_distintos,
       SUM((v.data_fim - v.data_inicio) + 1)          AS total_de_dias
  FROM viagem v
 WHERE v.id_usuario = 1
   AND v.data_fim < DATE '2026-05-01';


-- -----------------------------------------------------------------------------
-- 8. Custo estimado por dia e total da viagem
--    Tela: roteiro.html
--
--    GROUPING SETS produz, em uma única passagem, o subtotal de cada dia e o
--    total geral. A coluna "dia" vem nula na linha do total.
-- -----------------------------------------------------------------------------

SELECT d.ordem                      AS dia,
       SUM(a.custo_estimado)        AS custo
  FROM viagem v
  JOIN dia_roteiro       d ON d.id_viagem = v.id_viagem
  JOIN atividade_roteiro a ON a.id_dia    = d.id_dia
 WHERE v.id_viagem = 1
 GROUP BY GROUPING SETS ((d.ordem), ())
 ORDER BY d.ordem NULLS LAST;


-- -----------------------------------------------------------------------------
-- 9. RQ007 — Edição do roteiro: remover uma atividade
--
--    A exclusão em cascata definida no esquema remove também a nota pessoal
--    associada, sem necessidade de comando adicional.
-- -----------------------------------------------------------------------------

DELETE FROM atividade_roteiro
 WHERE id_atividade = 3;

-- Confirma que o dia 1 ficou com uma atividade a menos.
SELECT a.ordem_do_dia, l.nome
  FROM atividade_roteiro a
  JOIN local l ON l.id_local = a.id_local
 WHERE a.id_dia = 1
 ORDER BY a.ordem_do_dia;


-- -----------------------------------------------------------------------------
-- 10. RQ007 — Edição do roteiro: acrescentar uma atividade
--
--     A nova posição é calculada a partir da maior posição já ocupada no dia,
--     de modo que a atividade entre ao final sem violar a restrição de
--     unicidade entre dia e posição.
-- -----------------------------------------------------------------------------

INSERT INTO atividade_roteiro (id_dia, id_local, hora_sugerida, ordem_do_dia, custo_estimado)
SELECT 1,
       7,
       TIME '17:00',
       COALESCE(MAX(ordem_do_dia), 0) + 1,
       0.00
  FROM atividade_roteiro
 WHERE id_dia = 1;

SELECT a.ordem_do_dia, a.hora_sugerida, l.nome
  FROM atividade_roteiro a
  JOIN local l ON l.id_local = a.id_local
 WHERE a.id_dia = 1
 ORDER BY a.ordem_do_dia;


-- -----------------------------------------------------------------------------
-- 11. RQ008 — Notas pessoais de um usuário
--     Tela: roteiro.html
--
--     As notas são privadas: a consulta parte do usuário e só alcança as
--     atividades das viagens dele.
-- -----------------------------------------------------------------------------

SELECT v.destino,
       l.nome AS local,
       n.texto,
       n.criado_em
  FROM nota_pessoal       n
  JOIN atividade_roteiro  a ON a.id_atividade = n.id_atividade
  JOIN dia_roteiro        d ON d.id_dia       = a.id_dia
  JOIN viagem             v ON v.id_viagem    = d.id_viagem
  JOIN local              l ON l.id_local     = a.id_local
 WHERE v.id_usuario = 1
 ORDER BY n.criado_em;


-- -----------------------------------------------------------------------------
-- 12. Locais mais sugeridos pelo sistema
--
--     Justifica a decisão de manter local como entidade própria: o mesmo
--     ponto turístico é reaproveitado em roteiros diferentes, em vez de ter
--     endereço e coordenadas duplicados a cada viagem gerada.
-- -----------------------------------------------------------------------------

SELECT l.nome,
       COUNT(*) AS vezes_sugerido
  FROM atividade_roteiro a
  JOIN local l ON l.id_local = a.id_local
 GROUP BY l.nome
HAVING COUNT(*) >= 1
 ORDER BY vezes_sugerido DESC, l.nome
 LIMIT 5;
