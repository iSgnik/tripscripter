-- =============================================================================
-- TripScripter — Dados de exemplo
--
-- Carrega um conjunto mínimo de dados que permite demonstrar todos os
-- requisitos do sistema. Os roteiros de Paris e Tóquio são os mesmos
-- exibidos na aplicação web, de modo que a interface e o banco de dados
-- apresentem a mesma informação.
--
-- Execução, após 01-esquema.sql:
--   psql -U <usuario> -d tripscripter -f 02-dados-exemplo.sql
-- =============================================================================

-- Limpa os dados sem apagar a estrutura. RESTART IDENTITY devolve os
-- contadores das chaves primárias ao início, de modo que os identificadores
-- abaixo permaneçam válidos a cada nova carga.
TRUNCATE TABLE nota_pessoal, atividade_roteiro, dia_roteiro,
               viagem, preferencia, local, usuario
         RESTART IDENTITY CASCADE;


-- =============================================================================
-- Usuários
--
-- O campo senha_hash guarda um resumo criptográfico, nunca a senha em texto.
-- Os valores abaixo são ilustrativos, no formato bcrypt; no sistema final
-- serão gerados pela aplicação no momento do cadastro.
-- =============================================================================

INSERT INTO usuario (nome, email, senha_hash, data_cadastro) VALUES
    ('Marina Alves',   'marina@email.com', '$2b$12$exemploDeHashBcryptParaDemonstracao000000000000000000', '2026-01-15 09:20:00'),
    ('Rafael Nogueira','rafael@email.com', '$2b$12$outroHashBcryptIlustrativoParaDemonstracao0000000000', '2026-02-03 14:45:00');


-- =============================================================================
-- Preferências
--
-- Cada linha é um par categoria/nível. Marina tem interesse alto em cultura
-- e gastronomia; Rafael privilegia natureza.
-- =============================================================================

INSERT INTO preferencia (id_usuario, categoria, nivel_interesse) VALUES
    (1, 'Cultura',      5),
    (1, 'Gastronomia',  5),
    (1, 'Arte',         4),
    (1, 'Natureza',     2),
    (2, 'Natureza',     5),
    (2, 'Cultura',      3),
    (2, 'Vida noturna', 1);


-- =============================================================================
-- Catálogo de locais
--
-- As coordenadas são aproximadas e servem à demonstração; no sistema final
-- virão da geocodificação feita pelo serviço de mapas.
-- =============================================================================

INSERT INTO local (nome, endereco, latitude, longitude, horario_funcionamento, categoria) VALUES
    -- Paris (1 a 9)
    ('Musée de l''Orangerie',              'Jardin des Tuileries, 75001 Paris',        48.863800,   2.322600, 'Quarta a segunda, 9h às 18h', 'Arte'),
    ('Marché des Enfants Rouges',          '39 Rue de Bretagne, 75003 Paris',          48.863000,   2.362500, 'Terça a domingo, 8h30 às 19h30', 'Gastronomia'),
    ('Jardim de Luxemburgo',               '75006 Paris',                              48.846200,   2.337200, 'Diariamente, do amanhecer ao pôr do sol', 'Natureza'),
    ('Bistrot Paul Bert',                  '18 Rue Paul Bert, 75011 Paris',            48.852700,   2.383500, 'Terça a sábado, 12h às 14h e 19h30 às 23h', 'Gastronomia'),
    ('Montmartre',                         '75018 Paris',                              48.884600,   2.338000, 'Acesso livre', 'Cultura'),
    ('Basílica de Sacré-Cœur',             '35 Rue du Chevalier de la Barre, 75018',   48.886700,   2.343100, 'Diariamente, 6h30 às 22h30', 'Cultura'),
    ('Canal Saint-Martin',                 '75010 Paris',                              48.870900,   2.365800, 'Acesso livre', 'Natureza'),
    ('Museu do Louvre',                    'Rue de Rivoli, 75001 Paris',               48.860600,   2.337600, 'Quarta a segunda, 9h às 18h', 'Arte'),
    ('Livraria Shakespeare and Company',   '37 Rue de la Bûcherie, 75005 Paris',       48.852600,   2.347100, 'Diariamente, 10h às 22h', 'Cultura'),

    -- Tóquio (10 a 18)
    ('Templo Sensō-ji',                    '2-3-1 Asakusa, Taito, Tóquio',             35.714800, 139.796700, 'Diariamente, 6h às 17h', 'Cultura'),
    ('Rua Nakamise',                       '1-36-3 Asakusa, Taito, Tóquio',            35.711800, 139.796600, 'Diariamente, 9h às 19h', 'Gastronomia'),
    ('Jardim Nacional Shinjuku Gyoen',     '11 Naitomachi, Shinjuku, Tóquio',          35.685200, 139.710000, 'Terça a domingo, 9h às 16h30', 'Natureza'),
    ('Omoide Yokocho',                     '1-2 Nishishinjuku, Shinjuku, Tóquio',      35.693800, 139.699600, 'Diariamente, 17h às 23h', 'Vida noturna'),
    ('Museu Nacional de Tóquio',           '13-9 Uenokoen, Taito, Tóquio',             35.718800, 139.776600, 'Terça a domingo, 9h30 às 17h', 'Arte'),
    ('Parque Ueno',                        'Uenokoen, Taito, Tóquio',                  35.715600, 139.774500, 'Diariamente, 5h às 23h', 'Natureza'),
    ('Bairro de Yanaka',                   'Yanaka, Taito, Tóquio',                    35.727600, 139.766100, 'Acesso livre', 'Cultura'),
    ('Monte Takao',                        'Takaomachi, Hachioji, Tóquio',             35.625300, 139.243600, 'Acesso livre; teleférico das 8h às 17h45', 'Natureza'),
    ('Mirante de Shibuya',                 '2-24-12 Shibuya, Tóquio',                  35.658000, 139.701600, 'Diariamente, 10h às 22h30', 'Vida noturna'),

    -- Lisboa (19 a 21), usados na viagem já concluída
    ('Mosteiro dos Jerónimos',             'Praça do Império, 1400-206 Lisboa',        38.697700,  -9.206500, 'Terça a domingo, 10h às 17h30', 'Cultura'),
    ('Time Out Market',                    'Av. 24 de Julho 49, 1200-479 Lisboa',      38.707200,  -9.145800, 'Diariamente, 10h às 24h', 'Gastronomia'),
    ('Castelo de São Jorge',               'R. de Santa Cruz, 1100-129 Lisboa',        38.713900,  -9.133400, 'Diariamente, 9h às 21h', 'Cultura');


-- =============================================================================
-- Viagem 1 — Paris, de Marina (viagem futura)
-- =============================================================================

INSERT INTO viagem (id_usuario, destino, data_inicio, data_fim, estilo_viagem) VALUES
    (1, 'Paris, França', '2027-05-15', '2027-05-17', 'Equilibrado');

INSERT INTO dia_roteiro (id_viagem, data, ordem) VALUES
    (1, '2027-05-15', 1),
    (1, '2027-05-16', 2),
    (1, '2027-05-17', 3);

INSERT INTO atividade_roteiro (id_dia, id_local, hora_sugerida, ordem_do_dia, custo_estimado) VALUES
    -- Dia 1
    (1, 1, '09:00', 1, 12.00),
    (1, 2, '12:30', 2, 18.00),
    (1, 3, '15:00', 3,  0.00),
    (1, 4, '19:30', 4, 45.00),
    -- Dia 2
    (2, 5, '08:30', 1,  0.00),
    (2, 6, '11:00', 2,  0.00),
    (2, 7, '14:00', 3,  0.00),
    -- Dia 3
    (3, 8, '10:00', 1, 22.00),
    (3, 9, '16:00', 2,  0.00);


-- =============================================================================
-- Viagem 2 — Tóquio, de Rafael (viagem futura)
-- =============================================================================

INSERT INTO viagem (id_usuario, destino, data_inicio, data_fim, estilo_viagem) VALUES
    (2, 'Tóquio, Japão', '2027-06-10', '2027-06-12', 'Intenso');

INSERT INTO dia_roteiro (id_viagem, data, ordem) VALUES
    (2, '2027-06-10', 1),
    (2, '2027-06-11', 2),
    (2, '2027-06-12', 3);

INSERT INTO atividade_roteiro (id_dia, id_local, hora_sugerida, ordem_do_dia, custo_estimado) VALUES
    -- Dia 1
    (4, 10, '08:00', 1,     0.00),
    (4, 11, '11:00', 2,     0.00),
    (4, 12, '14:30', 3,   500.00),
    (4, 13, '19:00', 4,  3000.00),
    -- Dia 2
    (5, 14, '09:30', 1,  1000.00),
    (5, 15, '13:00', 2,     0.00),
    (5, 16, '16:00', 3,     0.00),
    -- Dia 3
    (6, 17, '07:30', 1,  1400.00),
    (6, 18, '18:00', 2,  2500.00);


-- =============================================================================
-- Viagem 3 — Lisboa, de Marina (viagem já concluída, usada no histórico)
-- =============================================================================

INSERT INTO viagem (id_usuario, destino, data_inicio, data_fim, estilo_viagem) VALUES
    (1, 'Lisboa, Portugal', '2026-04-10', '2026-04-11', 'Tranquilo');

INSERT INTO dia_roteiro (id_viagem, data, ordem) VALUES
    (3, '2026-04-10', 1),
    (3, '2026-04-11', 2);

INSERT INTO atividade_roteiro (id_dia, id_local, hora_sugerida, ordem_do_dia, custo_estimado) VALUES
    (7, 19, '10:00', 1, 10.00),
    (7, 20, '13:00', 2, 25.00),
    (8, 21, '09:30', 1, 15.00);


-- =============================================================================
-- Notas pessoais
-- =============================================================================

INSERT INTO nota_pessoal (id_atividade, texto, criado_em) VALUES
    (2, 'Chegar antes das 13h para evitar fila.',          '2026-04-20 21:10:00'),
    (8, 'Comprar o ingresso on-line na véspera.',           '2026-04-21 08:05:00'),
    (9, 'Procurar a seção de poesia no segundo andar.',     '2026-04-21 08:12:00'),
    (13, 'Levar água e calçado de trilha.',                 '2026-05-02 19:30:00');
