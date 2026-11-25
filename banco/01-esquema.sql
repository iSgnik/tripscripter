-- =============================================================================
-- TripScripter — Esquema do banco de dados
--
-- Implementa o modelo físico apresentado na Figura 5 do Documento de
-- Arquitetura de Software, seção 5.2. Sete tabelas, com chaves primárias
-- do tipo SERIAL e relacionamentos materializados por chaves estrangeiras.
--
-- Sistema gerenciador: PostgreSQL 16
--
-- Execução:
--   psql -U <usuario> -d tripscripter -f 01-esquema.sql
-- =============================================================================

-- Permite executar o script mais de uma vez durante o desenvolvimento.
-- A ordem respeita as dependências entre as tabelas.
DROP TABLE IF EXISTS nota_pessoal      CASCADE;
DROP TABLE IF EXISTS atividade_roteiro CASCADE;
DROP TABLE IF EXISTS dia_roteiro       CASCADE;
DROP TABLE IF EXISTS viagem            CASCADE;
DROP TABLE IF EXISTS preferencia       CASCADE;
DROP TABLE IF EXISTS local             CASCADE;
DROP TABLE IF EXISTS usuario           CASCADE;


-- =============================================================================
-- usuario — dados de cadastro e credenciais de acesso do turista (RQ001, RQ002)
-- =============================================================================

CREATE TABLE usuario (
    id_usuario    SERIAL       PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    email         VARCHAR(150) NOT NULL,
    senha_hash    VARCHAR(255) NOT NULL,
    data_cadastro TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- O e-mail identifica o usuário no login, portanto não pode repetir.
    CONSTRAINT uq_usuario_email UNIQUE (email),

    -- Validação mínima de formato; a validação completa cabe à aplicação.
    CONSTRAINT ck_usuario_email_formato CHECK (email LIKE '%_@_%._%'),

    CONSTRAINT ck_usuario_nome_vazio CHECK (length(trim(nome)) > 0)
);

COMMENT ON TABLE  usuario            IS 'Dados de cadastro e credenciais de acesso do turista';
COMMENT ON COLUMN usuario.senha_hash IS 'Resumo criptográfico da senha. A senha em texto puro nunca é armazenada';


-- =============================================================================
-- preferencia — categorias de interesse do usuário e o nível de cada uma
--
-- A tabela é normalizada: em vez de uma coluna booleana por categoria, cada
-- preferência é um par categoria/nível. Assim, incluir uma nova categoria de
-- atividade não exige alterar a estrutura do banco.
-- =============================================================================

CREATE TABLE preferencia (
    id_preferencia  SERIAL      PRIMARY KEY,
    id_usuario      INTEGER     NOT NULL,
    categoria       VARCHAR(50) NOT NULL,
    nivel_interesse SMALLINT    NOT NULL DEFAULT 3,

    CONSTRAINT fk_preferencia_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON DELETE CASCADE,

    -- Cada categoria aparece uma única vez por usuário.
    CONSTRAINT uq_preferencia_usuario_categoria UNIQUE (id_usuario, categoria),

    CONSTRAINT ck_preferencia_nivel CHECK (nivel_interesse BETWEEN 1 AND 5)
);

COMMENT ON TABLE  preferencia                 IS 'Categorias de atividade de interesse do usuário e o respectivo nível';
COMMENT ON COLUMN preferencia.nivel_interesse IS 'Escala de 1 (baixo) a 5 (alto), usada para ponderar as sugestões';


-- =============================================================================
-- viagem — destino, período e estilo de cada viagem planejada (RQ003)
-- =============================================================================

CREATE TABLE viagem (
    id_viagem     SERIAL       PRIMARY KEY,
    id_usuario    INTEGER      NOT NULL,
    destino       VARCHAR(120) NOT NULL,
    data_inicio   DATE         NOT NULL,
    data_fim      DATE         NOT NULL,
    estilo_viagem VARCHAR(50),

    CONSTRAINT fk_viagem_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON DELETE CASCADE,

    -- Uma viagem não pode terminar antes de começar.
    CONSTRAINT ck_viagem_periodo CHECK (data_fim >= data_inicio),

    CONSTRAINT ck_viagem_destino_vazio CHECK (length(trim(destino)) > 0)
);

COMMENT ON TABLE  viagem               IS 'Destino, período e estilo de cada viagem planejada';
COMMENT ON COLUMN viagem.estilo_viagem IS 'Ritmo desejado: tranquilo, equilibrado ou intenso';


-- =============================================================================
-- dia_roteiro — cada dia da viagem e sua ordem dentro do roteiro (RQ005)
--
-- Entidade central do modelo: é ela que permite registrar a que dia cada
-- atividade pertence. Sem ela, não haveria como organizar o roteiro por dias.
-- =============================================================================

CREATE TABLE dia_roteiro (
    id_dia    SERIAL   PRIMARY KEY,
    id_viagem INTEGER  NOT NULL,
    data      DATE     NOT NULL,
    ordem     SMALLINT NOT NULL,

    CONSTRAINT fk_dia_roteiro_viagem
        FOREIGN KEY (id_viagem) REFERENCES viagem (id_viagem)
        ON DELETE CASCADE,

    -- Não existem dois dias na mesma posição, nem duas vezes a mesma data.
    CONSTRAINT uq_dia_roteiro_ordem UNIQUE (id_viagem, ordem),
    CONSTRAINT uq_dia_roteiro_data  UNIQUE (id_viagem, data),

    CONSTRAINT ck_dia_roteiro_ordem CHECK (ordem > 0)
);

COMMENT ON TABLE  dia_roteiro       IS 'Cada dia da viagem e sua ordem dentro do roteiro';
COMMENT ON COLUMN dia_roteiro.ordem IS 'Posição do dia no roteiro, começando em 1';


-- =============================================================================
-- local — catálogo de pontos turísticos (RQ006)
--
-- Separado de atividade_roteiro porque o mesmo ponto turístico pode ser
-- sugerido em viagens diferentes, de usuários diferentes. Manter o local
-- como entidade própria evita duplicar endereço e coordenadas a cada roteiro.
--
-- A categoria fica no local, e não na atividade, porque é uma característica
-- do lugar: um museu é Cultura em qualquer roteiro em que apareça. Usa a
-- mesma classificação das preferências, o que permite comparar o roteiro
-- gerado com os interesses do usuário. Como em preferencia.categoria, os
-- valores aceitos são validados pela aplicação, e não por CHECK, para que
-- uma nova categoria não exija alterar a estrutura do banco.
-- =============================================================================

CREATE TABLE local (
    id_local               SERIAL        PRIMARY KEY,
    nome                   VARCHAR(150)  NOT NULL,
    endereco               VARCHAR(255),
    latitude               DECIMAL(9,6),
    longitude              DECIMAL(9,6),
    horario_funcionamento  VARCHAR(120),
    categoria              VARCHAR(50),

    -- Faixas válidas para coordenadas geográficas.
    CONSTRAINT ck_local_latitude  CHECK (latitude  BETWEEN  -90 AND  90),
    CONSTRAINT ck_local_longitude CHECK (longitude BETWEEN -180 AND 180),

    CONSTRAINT ck_local_nome_vazio CHECK (length(trim(nome)) > 0)
);

COMMENT ON TABLE  local           IS 'Catálogo de pontos turísticos, com endereço, coordenadas e horário de funcionamento';
COMMENT ON COLUMN local.latitude  IS 'Coordenada obtida por geocodificação; nula enquanto o local não for localizado';
COMMENT ON COLUMN local.categoria IS 'Mesma classificação usada em preferencia.categoria (Cultura, Gastronomia, Arte, Natureza, História, Compras, Vida noturna, Praia); nula se desconhecida';


-- =============================================================================
-- atividade_roteiro — atividade sugerida para um dia (RQ005, RQ007)
-- =============================================================================

CREATE TABLE atividade_roteiro (
    id_atividade   SERIAL        PRIMARY KEY,
    id_dia         INTEGER       NOT NULL,
    id_local       INTEGER       NOT NULL,
    hora_sugerida  TIME,
    ordem_do_dia   SMALLINT      NOT NULL,
    custo_estimado DECIMAL(10,2),

    CONSTRAINT fk_atividade_dia
        FOREIGN KEY (id_dia) REFERENCES dia_roteiro (id_dia)
        ON DELETE CASCADE,

    -- O catálogo de locais não é apagado junto com um roteiro.
    CONSTRAINT fk_atividade_local
        FOREIGN KEY (id_local) REFERENCES local (id_local)
        ON DELETE RESTRICT,

    -- Duas atividades não ocupam a mesma posição no mesmo dia.
    CONSTRAINT uq_atividade_ordem UNIQUE (id_dia, ordem_do_dia),

    CONSTRAINT ck_atividade_ordem CHECK (ordem_do_dia > 0),
    CONSTRAINT ck_atividade_custo CHECK (custo_estimado IS NULL OR custo_estimado >= 0)
);

COMMENT ON TABLE  atividade_roteiro                IS 'Atividade sugerida para um dia, com horário, ordem e custo estimado';
COMMENT ON COLUMN atividade_roteiro.ordem_do_dia   IS 'Posição da atividade dentro do dia; é o que o usuário altera ao reordenar o roteiro';
COMMENT ON COLUMN atividade_roteiro.custo_estimado IS 'Valor estimado na moeda local do destino';


-- =============================================================================
-- nota_pessoal — anotações privadas do usuário sobre uma atividade (RQ008)
-- =============================================================================

CREATE TABLE nota_pessoal (
    id_nota      SERIAL    PRIMARY KEY,
    id_atividade INTEGER   NOT NULL,
    texto        TEXT      NOT NULL,
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_nota_atividade
        FOREIGN KEY (id_atividade) REFERENCES atividade_roteiro (id_atividade)
        ON DELETE CASCADE,

    CONSTRAINT ck_nota_texto_vazio CHECK (length(trim(texto)) > 0)
);

COMMENT ON TABLE nota_pessoal IS 'Anotações privadas do usuário associadas a uma atividade do roteiro';


-- =============================================================================
-- Índices
--
-- As chaves estrangeiras recebem índice próprio porque são o caminho das
-- consultas mais frequentes: listar as viagens de um usuário, os dias de uma
-- viagem e as atividades de um dia. O PostgreSQL cria índice automaticamente
-- para chaves primárias e restrições de unicidade, mas não para estrangeiras.
-- =============================================================================

CREATE INDEX idx_preferencia_usuario ON preferencia       (id_usuario);
CREATE INDEX idx_viagem_usuario      ON viagem            (id_usuario);
CREATE INDEX idx_dia_roteiro_viagem  ON dia_roteiro       (id_viagem);
CREATE INDEX idx_atividade_dia       ON atividade_roteiro (id_dia);
CREATE INDEX idx_atividade_local     ON atividade_roteiro (id_local);
CREATE INDEX idx_nota_atividade      ON nota_pessoal      (id_atividade);

-- Consulta do histórico: viagens de um usuário já encerradas, da mais
-- recente para a mais antiga (RQ011).
CREATE INDEX idx_viagem_historico ON viagem (id_usuario, data_fim DESC);
