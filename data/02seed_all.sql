\set ON_ERROR_STOP on

\echo '== Limpando dados seedados anteriormente =='
TRUNCATE TABLE
  output_modelo,
  peso_features,
  aluno_disciplina,
  usuario_aluno,
  usuario_professor,
  usuario_coordenador,
  usuario_departamento,
  usuario_prorei,
  usuario_reitor,
  usuario_admin,
  documento_usuario,
  usuario,
  tipo_proreitoria,
  aluno,
  disciplina,
  curso,
  departamento,
  periodo,
  categoria_usuario,
  unidade,
  campus
RESTART IDENTITY CASCADE;

\echo '== Importando CSVs base (CAMPUS, UNIDADE, CATEGORIA_USUARIO, DEPARTAMENTO, PERIODO, CURSO, DISCIPLINA) =='
\copy campus(id_campus, nome_campus) FROM '/csvdata/CAMPUS.csv' DELIMITER ',' CSV HEADER;
\copy unidade(id_unidade, id_campus, nome_unidade) FROM '/csvdata/UNIDADE.csv' DELIMITER ',' CSV HEADER;
\copy categoria_usuario(id_categoria_usuario, nome_categoria) FROM '/csvdata/CATEGORIA_USUARIO.csv' DELIMITER ',' CSV HEADER;
\copy departamento(id_departamento, id_unidade, nome_departamento) FROM '/csvdata/DEPARTAMENTO.csv' DELIMITER ',' CSV HEADER;
\copy periodo(id_periodo, periodo) FROM '/csvdata/PERIODO.csv' DELIMITER ',' CSV HEADER;
\copy curso(id_curso, id_unidade, id_periodo, nome_curso, modalidade) FROM '/csvdata/CURSO.csv' DELIMITER ',' CSV HEADER;

\echo '== Importando ALUNO.csv com staging =='
DROP TABLE IF EXISTS stg_aluno;
CREATE TEMP TABLE stg_aluno (
  id_aluno_graduacao TEXT,
  cidade_origem TEXT,
  raca_cor TEXT,
  sexo TEXT,
  ensino_medio TEXT,
  cotas TEXT,
  tipo_ingresso TEXT,
  situacao TEXT,
  ano_matricula TEXT,
  avg_nota TEXT,
  max_nota TEXT,
  min_nota TEXT,
  median_nota TEXT,
  avg_frequencia TEXT,
  max_frequencia TEXT,
  min_frequencia TEXT,
  median_frequencia TEXT,
  perc_reprovacao TEXT,
  perc_exames TEXT,
  qtd_disciplinas TEXT,
  ano_nascimento TEXT,
  mes_nascimento TEXT,
  idade_matricula TEXT,
  distancia_campus TEXT,
  id_periodo TEXT,
  id_curso TEXT
);

\copy stg_aluno FROM '/csvdata/ALUNO.csv' DELIMITER ',' CSV HEADER;

INSERT INTO aluno (
  id_aluno_graduacao,
  id_curso,
  raca_cor,
  sexo,
  ano_nascimento,
  ensino_medio,
  cidade_origem,
  cotas,
  tipo_ingresso,
  ano_matricula,
  situacao,
  max_nota,
  min_nota,
  avg_nota,
  median_nota,
  unique_disciplinas,
  max_frequencia,
  min_frequencia,
  avg_frequencia,
  median_frequencia,
  idade_matricula,
  distancia_campus,
  perc_reprovacao,
  perc_exames
)
SELECT DISTINCT ON (id_aluno_graduacao_int)
  id_aluno_graduacao_int,
  id_curso_int,
  raca_cor_val,
  sexo_val,
  ano_nascimento_int,
  ensino_medio_val,
  cidade_origem_val,
  cotas_val,
  tipo_ingresso_val,
  ano_matricula_int,
  situacao_val,
  max_nota_val,
  min_nota_val,
  avg_nota_val,
  median_nota_val,
  qtd_disciplinas_int,
  max_frequencia_val,
  min_frequencia_val,
  avg_frequencia_val,
  median_frequencia_val,
  idade_matricula_int,
  distancia_campus_val,
  perc_reprovacao_val,
  perc_exames_val
FROM (
  SELECT
    NULLIF(BTRIM(id_aluno_graduacao), '')::INTEGER AS id_aluno_graduacao_int,
    NULLIF(BTRIM(id_curso), '')::INTEGER AS id_curso_int,
    NULLIF(BTRIM(raca_cor), '') AS raca_cor_val,
    NULLIF(BTRIM(sexo), '') AS sexo_val,
    CAST(NULLIF(BTRIM(ano_nascimento), '') AS DECIMAL)::INTEGER AS ano_nascimento_int,
    NULLIF(BTRIM(ensino_medio), '') AS ensino_medio_val,
    NULLIF(BTRIM(cidade_origem), '') AS cidade_origem_val,
    NULLIF(BTRIM(cotas), '') AS cotas_val,
    NULLIF(BTRIM(tipo_ingresso), '') AS tipo_ingresso_val,
    CAST(NULLIF(BTRIM(ano_matricula), '') AS DECIMAL)::INTEGER AS ano_matricula_int,
    NULLIF(BTRIM(situacao), '') AS situacao_val,
    NULLIF(BTRIM(max_nota), '')::DECIMAL AS max_nota_val,
    NULLIF(BTRIM(min_nota), '')::DECIMAL AS min_nota_val,
    NULLIF(BTRIM(avg_nota), '')::DECIMAL AS avg_nota_val,
    NULLIF(BTRIM(median_nota), '')::DECIMAL AS median_nota_val,
    CAST(NULLIF(BTRIM(qtd_disciplinas), '') AS DECIMAL)::INTEGER AS qtd_disciplinas_int,
    NULLIF(BTRIM(max_frequencia), '')::DECIMAL AS max_frequencia_val,
    NULLIF(BTRIM(min_frequencia), '')::DECIMAL AS min_frequencia_val,
    NULLIF(BTRIM(avg_frequencia), '')::DECIMAL AS avg_frequencia_val,
    NULLIF(BTRIM(median_frequencia), '')::DECIMAL AS median_frequencia_val,
    CAST(NULLIF(BTRIM(idade_matricula), '') AS DECIMAL)::INTEGER AS idade_matricula_int,
    NULLIF(BTRIM(distancia_campus), '')::DECIMAL AS distancia_campus_val,
    NULLIF(BTRIM(perc_reprovacao), '')::DECIMAL AS perc_reprovacao_val,
    NULLIF(BTRIM(perc_exames), '')::DECIMAL AS perc_exames_val
  FROM stg_aluno
  WHERE NULLIF(BTRIM(id_aluno_graduacao), '') IS NOT NULL
    AND NULLIF(BTRIM(id_curso), '') IS NOT NULL
) s
ORDER BY
  id_aluno_graduacao_int,
  ano_matricula_int DESC NULLS LAST,
  qtd_disciplinas_int DESC NULLS LAST,
  avg_nota_val DESC NULLS LAST;

\echo '== Importando DISCIPLINA.csv com staging =='
DROP TABLE IF EXISTS stg_disciplina;
CREATE TEMP TABLE stg_disciplina (
  id_disciplina TEXT,
  id_curso TEXT,
  id_aluno_graduacao TEXT,
  nome_disciplina TEXT,
  conceito TEXT,
  frequencia TEXT,
  tipo_efetivacao TEXT,
  tipo_nota TEXT,
  nota TEXT
);

\copy stg_disciplina FROM '/csvdata/DISCIPLINA.csv' DELIMITER ',' CSV HEADER;

INSERT INTO disciplina (
  id_disciplina,
  id_curso,
  nome_disciplina,
  nome_disciplina_normalizado
)
SELECT DISTINCT
  NULLIF(BTRIM(id_disciplina), '')::INTEGER,
  NULLIF(BTRIM(id_curso), '')::INTEGER,
  NULLIF(BTRIM(nome_disciplina), ''),
  lower(trim(regexp_replace(unaccent(NULLIF(BTRIM(nome_disciplina), '')), '[[:space:]]+', ' ', 'g')))
FROM stg_disciplina
WHERE NULLIF(BTRIM(id_disciplina), '') IS NOT NULL
  AND NULLIF(BTRIM(id_curso), '') IS NOT NULL
  AND NULLIF(BTRIM(nome_disciplina), '') IS NOT NULL;

INSERT INTO aluno_disciplina (
  id_aluno_graduacao,
  id_disciplina,
  conceito,
  frequencia,
  tipo_efetivacao,
  tipo_nota,
  nota
)
SELECT
  sd.id_aluno_graduacao_int,
  sd.id_disciplina_int,
  sd.conceito_val,
  sd.frequencia_val,
  sd.tipo_efetivacao_val,
  sd.tipo_nota_val,
  sd.nota_val
FROM (
  SELECT
    NULLIF(BTRIM(id_aluno_graduacao), '')::INTEGER AS id_aluno_graduacao_int,
    NULLIF(BTRIM(id_disciplina), '')::INTEGER AS id_disciplina_int,
    NULLIF(BTRIM(conceito), '') AS conceito_val,
    NULLIF(BTRIM(frequencia), '')::DECIMAL AS frequencia_val,
    NULLIF(BTRIM(tipo_efetivacao), '') AS tipo_efetivacao_val,
    NULLIF(BTRIM(tipo_nota), '') AS tipo_nota_val,
    NULLIF(BTRIM(nota), '')::DECIMAL AS nota_val
  FROM stg_disciplina
  WHERE NULLIF(BTRIM(id_aluno_graduacao), '') IS NOT NULL
    AND NULLIF(BTRIM(id_disciplina), '') IS NOT NULL
) sd
JOIN aluno a
  ON a.id_aluno_graduacao = sd.id_aluno_graduacao_int
JOIN disciplina d
  ON d.id_disciplina = sd.id_disciplina_int;

\echo '== Importando OUTPUT_MODELO.csv com staging =='
DROP TABLE IF EXISTS stg_output_modelo;
CREATE TEMP TABLE stg_output_modelo (
  id_aluno_graduacao TEXT,
  classificacao TEXT
);
\copy stg_output_modelo FROM '/csvdata/OUTPUT_MODELO.csv' DELIMITER ',' CSV HEADER;

INSERT INTO output_modelo (id_aluno_graduacao, classificacao)
SELECT DISTINCT ON (som.id_aluno_graduacao_int)
  som.id_aluno_graduacao_int,
  som.classificacao_val
FROM (
  SELECT
    CAST(NULLIF(BTRIM(id_aluno_graduacao), '') AS DECIMAL)::INTEGER AS id_aluno_graduacao_int,
    NULLIF(BTRIM(classificacao), '')::DECIMAL AS classificacao_val
  FROM stg_output_modelo
  WHERE NULLIF(BTRIM(id_aluno_graduacao), '') IS NOT NULL
) som
JOIN aluno a
  ON a.id_aluno_graduacao = som.id_aluno_graduacao_int
ORDER BY som.id_aluno_graduacao_int, som.classificacao_val DESC NULLS LAST;

\echo '== Importando PESO_FEATURES.csv com staging =='
DROP TABLE IF EXISTS stg_peso_features;
CREATE TEMP TABLE stg_peso_features (
  id_aluno_graduacao TEXT,
  feature TEXT,
  peso TEXT,
  descricao TEXT
);
\copy stg_peso_features FROM '/csvdata/PESO_FEATURES.csv' DELIMITER ',' CSV HEADER;

INSERT INTO peso_features (id_aluno_graduacao, feature, peso, descricao)
SELECT
  spf.id_aluno_graduacao_int,
  spf.feature_val,
  spf.peso_val,
  spf.descricao_val
FROM (
  SELECT
    CAST(NULLIF(BTRIM(id_aluno_graduacao), '') AS DECIMAL)::INTEGER AS id_aluno_graduacao_int,
    NULLIF(BTRIM(feature), '') AS feature_val,
    NULLIF(BTRIM(peso), '')::DECIMAL AS peso_val,
    NULLIF(BTRIM(descricao), '') AS descricao_val
  FROM stg_peso_features
  WHERE NULLIF(BTRIM(id_aluno_graduacao), '') IS NOT NULL
    AND NULLIF(BTRIM(feature), '') IS NOT NULL
) spf
JOIN aluno a
  ON a.id_aluno_graduacao = spf.id_aluno_graduacao_int;

\echo '== Ajustando sequences após imports =='
SELECT setval(pg_get_serial_sequence('campus', 'id_campus'), COALESCE((SELECT MAX(id_campus) FROM campus), 1), true);
SELECT setval(pg_get_serial_sequence('unidade', 'id_unidade'), COALESCE((SELECT MAX(id_unidade) FROM unidade), 1), true);
SELECT setval(pg_get_serial_sequence('categoria_usuario', 'id_categoria_usuario'), COALESCE((SELECT MAX(id_categoria_usuario) FROM categoria_usuario), 1), true);
SELECT setval(pg_get_serial_sequence('departamento', 'id_departamento'), COALESCE((SELECT MAX(id_departamento) FROM departamento), 1), true);
SELECT setval(pg_get_serial_sequence('periodo', 'id_periodo'), COALESCE((SELECT MAX(id_periodo) FROM periodo), 1), true);
SELECT setval(pg_get_serial_sequence('curso', 'id_curso'), COALESCE((SELECT MAX(id_curso) FROM curso), 1), true);
SELECT setval(pg_get_serial_sequence('disciplina', 'id_disciplina'), COALESCE((SELECT MAX(id_disciplina) FROM disciplina), 1), true);
SELECT setval(pg_get_serial_sequence('aluno', 'id_aluno_graduacao'), COALESCE((SELECT MAX(id_aluno_graduacao) FROM aluno), 1), true);
SELECT setval(pg_get_serial_sequence('peso_features', 'id_feature'), COALESCE((SELECT MAX(id_feature) FROM peso_features), 1), true);

\echo '== Seed consistente de tipos de pró-reitoria =='
INSERT INTO tipo_proreitoria (nome_proreitoria)
VALUES
  ('Graduação'),
  ('Pesquisa'),
  ('Extensão');

\echo '== Seed consistente de usuários e vínculos =='
DO $$
DECLARE
  v_campus_1 INT;
  v_campus_2 INT;
  v_unidade_1 INT;
  v_unidade_2 INT;
  v_departamento_1 INT;
  v_departamento_2 INT;
  v_curso_1 INT;
  v_curso_2 INT;
  v_disciplina_1 INT;
  v_disciplina_2 INT;
  v_aluno_1 INT;
  v_aluno_2 INT;

  v_tipo_proreitoria_id INT;

  v_cat_admin INT;
  v_cat_reitoria INT;
  v_cat_proreitoria INT;
  v_cat_dep INT;
  v_cat_coord INT;
  v_cat_prof INT;
  v_cat_aluno INT;

  v_admin_user INT;
  v_reitoria_user INT;
  v_prorei_user INT;
  v_dep_user INT;
  v_coord_user INT;
  v_prof_user INT;
  v_aluno_user INT;
  v_prof_pendente_user INT;
  v_aluno_pendente_user INT;
  v_dep_rejeitado_user INT;
BEGIN
    -- Base principal: escolhe um conjunto consistente com campus -> unidade -> curso -> disciplina -> aluno
  SELECT
    ca.id_campus,
    un.id_unidade,
    c.id_curso,
    d.id_disciplina,
    a.id_aluno_graduacao
  INTO
    v_campus_1,
    v_unidade_1,
    v_curso_1,
    v_disciplina_1,
    v_aluno_1
  FROM unidade un
  JOIN campus ca
    ON ca.id_campus = un.id_campus
  JOIN curso c
    ON c.id_unidade = un.id_unidade
  JOIN disciplina d
    ON d.id_curso = c.id_curso
  JOIN aluno a
    ON a.id_curso = c.id_curso
  ORDER BY ca.id_campus, un.id_unidade, c.id_curso, d.id_disciplina, a.id_aluno_graduacao
  LIMIT 1;

  -- Base secundária: tenta pegar outro conjunto consistente diferente do principal
  SELECT
    ca.id_campus,
    un.id_unidade,
    c.id_curso,
    d.id_disciplina,
    a.id_aluno_graduacao
  INTO
    v_campus_2,
    v_unidade_2,
    v_curso_2,
    v_disciplina_2,
    v_aluno_2
  FROM unidade un
  JOIN campus ca
    ON ca.id_campus = un.id_campus
  JOIN curso c
    ON c.id_unidade = un.id_unidade
  JOIN disciplina d
    ON d.id_curso = c.id_curso
  JOIN aluno a
    ON a.id_curso = c.id_curso
  WHERE
    ca.id_campus <> v_campus_1
    OR un.id_unidade <> v_unidade_1
    OR c.id_curso <> v_curso_1
    OR d.id_disciplina <> v_disciplina_1
    OR a.id_aluno_graduacao <> v_aluno_1
  ORDER BY ca.id_campus, un.id_unidade, c.id_curso, d.id_disciplina, a.id_aluno_graduacao
  LIMIT 1;

  IF v_campus_2 IS NULL THEN v_campus_2 := v_campus_1; END IF;
  IF v_unidade_2 IS NULL THEN v_unidade_2 := v_unidade_1; END IF;
  IF v_curso_2 IS NULL THEN v_curso_2 := v_curso_1; END IF;
  IF v_disciplina_2 IS NULL THEN v_disciplina_2 := v_disciplina_1; END IF;
  IF v_aluno_2 IS NULL THEN v_aluno_2 := v_aluno_1; END IF;

  -- Departamentos vinculados às unidades escolhidas
  SELECT id_departamento
  INTO v_departamento_1
  FROM departamento
  WHERE id_unidade = v_unidade_1
  ORDER BY id_departamento
  LIMIT 1;

  IF v_departamento_1 IS NULL THEN
    SELECT id_departamento, id_unidade
    INTO v_departamento_1, v_unidade_1
    FROM departamento
    ORDER BY id_departamento
    LIMIT 1;
  END IF;

  SELECT id_departamento
  INTO v_departamento_2
  FROM departamento
  WHERE id_unidade = v_unidade_2
    AND id_departamento <> v_departamento_1
  ORDER BY id_departamento
  LIMIT 1;

  IF v_departamento_2 IS NULL THEN
    SELECT id_departamento
    INTO v_departamento_2
    FROM departamento
    WHERE id_departamento <> v_departamento_1
    ORDER BY id_departamento
    LIMIT 1;
  END IF;

  IF v_departamento_2 IS NULL THEN v_departamento_2 := v_departamento_1; END IF;

  IF v_campus_1 IS NULL OR v_unidade_1 IS NULL OR v_curso_1 IS NULL OR v_disciplina_1 IS NULL OR v_aluno_1 IS NULL THEN
    RAISE EXCEPTION 'Dados-base insuficientes após import. Verifique a interseção real entre UNIDADE, CURSO, DISCIPLINA e ALUNO.';
  END IF;

  SELECT id_categoria_usuario INTO v_cat_admin
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%admin%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_reitoria
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%reitor%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_proreitoria
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%pro%reitor%'
     OR lower(trim(nome_categoria)) LIKE '%pró%reitor%'
     OR lower(trim(nome_categoria)) LIKE '%proreitor%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_dep
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%depart%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_coord
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%coord%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_prof
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%prof%'
  ORDER BY id_categoria_usuario LIMIT 1;

  SELECT id_categoria_usuario INTO v_cat_aluno
  FROM categoria_usuario
  WHERE lower(trim(nome_categoria)) LIKE '%aluno%'
  ORDER BY id_categoria_usuario LIMIT 1;

  IF v_cat_admin IS NULL OR v_cat_reitoria IS NULL OR v_cat_proreitoria IS NULL OR v_cat_dep IS NULL OR v_cat_coord IS NULL OR v_cat_prof IS NULL OR v_cat_aluno IS NULL THEN
    RAISE EXCEPTION 'Nem todas as categorias necessárias foram encontradas em CATEGORIA_USUARIO.csv';
  END IF;

  SELECT id_tipo_proreitoria INTO v_tipo_proreitoria_id
  FROM tipo_proreitoria
  ORDER BY id_tipo_proreitoria
  LIMIT 1;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_admin, 'Admin de Teste', 'admin.teste@unesp.br', '11111111111', '(11) 99999-0001', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_admin_user;
  INSERT INTO usuario_admin (id_usuario, id_campus) VALUES (v_admin_user, v_campus_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_reitoria, 'Reitoria de Teste', 'reitoria.teste@unesp.br', '11111111112', '(11) 99999-0002', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_reitoria_user;
  INSERT INTO usuario_reitor (id_usuario, id_campus) VALUES (v_reitoria_user, v_campus_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_proreitoria, 'Pró-Reitoria de Teste', 'proreitoria.teste@unesp.br', '11111111113', '(11) 99999-0003', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_prorei_user;
  INSERT INTO usuario_prorei (id_usuario, id_campus, id_proreitoria) VALUES (v_prorei_user, v_campus_1, v_tipo_proreitoria_id);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_dep, 'Departamento de Teste', 'departamento.teste@unesp.br', '11111111114', '(11) 99999-0004', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_dep_user;
  INSERT INTO usuario_departamento (id_usuario, id_unidade, id_departamento) VALUES (v_dep_user, v_unidade_1, v_departamento_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_coord, 'Coordenação de Teste', 'coordenacao.teste@unesp.br', '11111111115', '(11) 99999-0005', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_coord_user;
  INSERT INTO usuario_coordenador (id_usuario, id_unidade, id_curso) VALUES (v_coord_user, v_unidade_1, v_curso_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_prof, 'Professor de Teste', 'professor.teste@unesp.br', '11111111116', '(11) 99999-0006', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_prof_user;
  INSERT INTO usuario_professor (id_usuario, id_unidade, id_disciplina) VALUES (v_prof_user, v_unidade_1, v_disciplina_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno de Teste', 'aluno.teste@unesp.br', '11111111117', '(11) 99999-0007', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_user;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_user, v_unidade_1, v_aluno_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_prof, 'Professor Pendente de Teste', 'professor.pendente@unesp.br', '11111111118', '(11) 99999-0008', 'PENDENTE', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_prof_pendente_user;
  INSERT INTO usuario_professor (id_usuario, id_unidade, id_disciplina) VALUES (v_prof_pendente_user, v_unidade_2, v_disciplina_2);

  INSERT INTO documento_usuario (
    id_usuario, tipo_documento, storage_provider, storage_bucket, storage_key, hash_arquivo,
    mime_type, tamanho_arquivo, status_analise
  ) VALUES (
    v_prof_pendente_user, 'COMPROVANTE_VINCULO', 'local', NULL,
    'seed/professor-pendente-comprovante.pdf', md5('professor-pendente-comprovante'),
    'application/pdf', 102400, 'PENDENTE'
  );

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno Pendente de Teste', 'aluno.pendente@unesp.br', '11111111119', '(11) 99999-0009', 'PENDENTE', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_pendente_user;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_pendente_user, v_unidade_2, v_aluno_2);

  INSERT INTO documento_usuario (
    id_usuario, tipo_documento, storage_provider, storage_bucket, storage_key, hash_arquivo,
    mime_type, tamanho_arquivo, status_analise
  ) VALUES (
    v_aluno_pendente_user, 'HISTORICO_ESCOLAR', 'local', NULL,
    'seed/aluno-pendente-historico.pdf', md5('aluno-pendente-historico'),
    'application/pdf', 204800, 'PENDENTE'
  );

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_dep, 'Departamento Rejeitado de Teste', 'departamento.rejeitado@unesp.br', '11111111120', '(11) 99999-0010', 'REJEITADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_dep_rejeitado_user;
  INSERT INTO usuario_departamento (id_usuario, id_unidade, id_departamento) VALUES (v_dep_rejeitado_user, v_unidade_2, v_departamento_2);

  INSERT INTO documento_usuario (
    id_usuario, tipo_documento, storage_provider, storage_bucket, storage_key, hash_arquivo,
    mime_type, tamanho_arquivo, status_analise
  ) VALUES (
    v_dep_rejeitado_user, 'PORTARIA', 'local', NULL,
    'seed/departamento-rejeitado-portaria.pdf', md5('departamento-rejeitado-portaria'),
    'application/pdf', 51200, 'REJEITADO'
  );
END $$;

\echo '== Ajustando sequences finais após seed de usuários =='
SELECT setval(pg_get_serial_sequence('tipo_proreitoria', 'id_tipo_proreitoria'), COALESCE((SELECT MAX(id_tipo_proreitoria) FROM tipo_proreitoria), 1), true);
SELECT setval(pg_get_serial_sequence('usuario', 'id_usuario'), COALESCE((SELECT MAX(id_usuario) FROM usuario), 1), true);
SELECT setval(pg_get_serial_sequence('documento_usuario', 'id_documento'), COALESCE((SELECT MAX(id_documento) FROM documento_usuario), 1), true);

\echo '== Conferência rápida =='
SELECT 'campus' AS tabela, COUNT(*) AS qtd FROM campus;
SELECT 'unidade' AS tabela, COUNT(*) AS qtd FROM unidade;
SELECT 'categoria_usuario' AS tabela, COUNT(*) AS qtd FROM categoria_usuario;
SELECT 'departamento' AS tabela, COUNT(*) AS qtd FROM departamento;
SELECT 'periodo' AS tabela, COUNT(*) AS qtd FROM periodo;
SELECT 'curso' AS tabela, COUNT(*) AS qtd FROM curso;
SELECT 'disciplina' AS tabela, COUNT(*) AS qtd FROM disciplina;
SELECT 'aluno' AS tabela, COUNT(*) AS qtd FROM aluno;
SELECT 'output_modelo' AS tabela, COUNT(*) AS qtd FROM output_modelo;
SELECT 'peso_features' AS tabela, COUNT(*) AS qtd FROM peso_features;
SELECT 'usuario' AS tabela, COUNT(*) AS qtd FROM usuario;
SELECT 'documento_usuario' AS tabela, COUNT(*) AS qtd FROM documento_usuario;