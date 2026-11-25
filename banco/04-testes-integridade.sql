\set ON_ERROR_STOP off

DO $$
DECLARE
    total  INTEGER := 0;
    passou INTEGER := 0;
BEGIN

    -- -------------------------------------------------------------------------
    RAISE NOTICE '--- Restrições de unicidade ---';

    total := total + 1;
    BEGIN
        INSERT INTO usuario (nome, email, senha_hash)
        VALUES ('Impostor', 'marina@email.com', 'hash');
        RAISE NOTICE 'FALHOU  e-mail repetido foi aceito';
    EXCEPTION WHEN unique_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      e-mail repetido rejeitado';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO preferencia (id_usuario, categoria, nivel_interesse)
        VALUES (1, 'Cultura', 4);
        RAISE NOTICE 'FALHOU  categoria repetida para o mesmo usuário foi aceita';
    EXCEPTION WHEN unique_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      categoria repetida para o mesmo usuário rejeitada';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO atividade_roteiro (id_dia, id_local, ordem_do_dia)
        VALUES (1, 5, 1);
        RAISE NOTICE 'FALHOU  duas atividades na mesma posição do dia foram aceitas';
    EXCEPTION WHEN unique_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      duas atividades na mesma posição do dia rejeitadas';
    END;

    -- -------------------------------------------------------------------------
    RAISE NOTICE '--- Restrições de domínio ---';

    total := total + 1;
    BEGIN
        INSERT INTO viagem (id_usuario, destino, data_inicio, data_fim)
        VALUES (1, 'Roma, Itália', '2026-07-10', '2026-07-01');
        RAISE NOTICE 'FALHOU  viagem terminando antes de começar foi aceita';
    EXCEPTION WHEN check_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      viagem terminando antes de começar rejeitada';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO preferencia (id_usuario, categoria, nivel_interesse)
        VALUES (1, 'Praia', 9);
        RAISE NOTICE 'FALHOU  nível de interesse fora da escala foi aceito';
    EXCEPTION WHEN check_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      nível de interesse fora da escala rejeitado';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO local (nome, latitude, longitude)
        VALUES ('Lugar impossível', 120.0, 0.0);
        RAISE NOTICE 'FALHOU  latitude fora da faixa válida foi aceita';
    EXCEPTION WHEN check_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      latitude fora da faixa válida rejeitada';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO atividade_roteiro (id_dia, id_local, ordem_do_dia, custo_estimado)
        VALUES (2, 5, 9, -50.00);
        RAISE NOTICE 'FALHOU  custo negativo foi aceito';
    EXCEPTION WHEN check_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      custo negativo rejeitado';
    END;

    total := total + 1;
    BEGIN
        INSERT INTO usuario (nome, email, senha_hash)
        VALUES ('Sem arroba', 'email-invalido', 'hash');
        RAISE NOTICE 'FALHOU  e-mail sem formato válido foi aceito';
    EXCEPTION WHEN check_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      e-mail sem formato válido rejeitado';
    END;

    -- -------------------------------------------------------------------------
    RAISE NOTICE '--- Integridade referencial ---';

    total := total + 1;
    BEGIN
        INSERT INTO viagem (id_usuario, destino, data_inicio, data_fim)
        VALUES (9999, 'Viagem órfã', '2026-07-01', '2026-07-05');
        RAISE NOTICE 'FALHOU  viagem de usuário inexistente foi aceita';
    EXCEPTION WHEN foreign_key_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      viagem de usuário inexistente rejeitada';
    END;

    total := total + 1;
    BEGIN
        DELETE FROM local WHERE id_local = 1;
        RAISE NOTICE 'FALHOU  local em uso por um roteiro foi apagado';
    EXCEPTION WHEN foreign_key_violation THEN
        passou := passou + 1;
        RAISE NOTICE 'ok      local em uso por um roteiro protegido contra exclusão';
    END;

    -- -------------------------------------------------------------------------
    RAISE NOTICE '--- Resultado: % de % testes passaram ---', passou, total;

    IF passou <> total THEN
        RAISE EXCEPTION 'Nem todas as restrições estão em vigor';
    END IF;
END $$;


-- =============================================================================
-- Exclusão em cascata
--
-- Apagar uma viagem deve remover seus dias, atividades e notas, sem deixar
-- registros órfãos. O teste roda dentro de uma transação desfeita ao final,
-- de modo que os dados de exemplo permaneçam intactos.
-- =============================================================================

BEGIN;

SELECT 'antes' AS momento,
       (SELECT COUNT(*) FROM dia_roteiro       WHERE id_viagem = 1) AS dias,
       (SELECT COUNT(*) FROM atividade_roteiro a
          JOIN dia_roteiro d ON d.id_dia = a.id_dia
         WHERE d.id_viagem = 1)                                     AS atividades,
       (SELECT COUNT(*) FROM nota_pessoal      n
          JOIN atividade_roteiro a ON a.id_atividade = n.id_atividade
          JOIN dia_roteiro d ON d.id_dia = a.id_dia
         WHERE d.id_viagem = 1)                                     AS notas;

DELETE FROM viagem WHERE id_viagem = 1;

SELECT 'depois' AS momento,
       (SELECT COUNT(*) FROM dia_roteiro       WHERE id_viagem = 1) AS dias,
       (SELECT COUNT(*) FROM atividade_roteiro a
          JOIN dia_roteiro d ON d.id_dia = a.id_dia
         WHERE d.id_viagem = 1)                                     AS atividades,
       (SELECT COUNT(*) FROM nota_pessoal      n
          JOIN atividade_roteiro a ON a.id_atividade = n.id_atividade
          JOIN dia_roteiro d ON d.id_dia = a.id_dia
         WHERE d.id_viagem = 1)                                     AS notas;

ROLLBACK;
