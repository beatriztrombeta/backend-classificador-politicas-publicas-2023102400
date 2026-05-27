\set ON_ERROR_STOP on

-- =========================
-- TABELA DE LOG DE IMPORTAÇÃO
-- =========================
DROP TABLE IF EXISTS import_statistics CASCADE;
CREATE TABLE import_statistics (
  id SERIAL PRIMARY KEY,
  tabela VARCHAR NOT NULL,
  linhas_origem INTEGER,
  linhas_inseridas INTEGER,
  linhas_descartadas INTEGER,
  linhas_com_erro INTEGER,
  motivos_descarte TEXT,
  tempo_processamento_ms INTEGER,
  data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS dados_descartados_log CASCADE;
CREATE TABLE dados_descartados_log (
  id SERIAL PRIMARY KEY,
  tabela_origem VARCHAR,
  id_original_texto VARCHAR,
  motivo_descarte VARCHAR,
  valor_descartado TEXT,
  data_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS import_status CASCADE;
CREATE TABLE import_status (
  chave TEXT PRIMARY KEY,
  valor TEXT NOT NULL,
  atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\echo '== Limpando dados seedados anteriormente =='
TRUNCATE TABLE
  dados_descartados_log,
  import_statistics,
  import_status,
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

\echo '== Importando ALUNO.csv SEM remover duplicatas (mantenha os dados originais) =='
DROP TABLE IF EXISTS stg_aluno;
CREATE TEMP TABLE stg_aluno (
  id_aluno_graduacao TEXT,
  raca_cor TEXT,
  sexo TEXT,
  ano_nascimento TEXT,
  ensino_medio TEXT,
  cidade_origem TEXT,
  estado_origem TEXT,
  pais_origem TEXT,
  cotas TEXT,
  tipo_ingresso TEXT,
  forma_ingresso TEXT,
  ano_matricula TEXT,
  situacao TEXT,
  motivo_desvinculo TEXT,
  data_desvinculo TEXT,
  cr TEXT,
  max_nota TEXT,
  min_nota TEXT,
  avg_nota TEXT,
  median_nota TEXT,
  unique_disciplinas TEXT,
  max_frequencia TEXT,
  min_frequencia TEXT,
  avg_frequencia TEXT,
  median_frequencia TEXT,
  idade_matricula TEXT,
  perc_reprovacao TEXT,
  perc_exames TEXT,
  distancia_campus TEXT,
  id_curso TEXT,
  id_periodo TEXT
);

\copy stg_aluno FROM '/csvdata/ALUNO.csv' DELIMITER ',' CSV HEADER;

-- Verificar quantas linhas foram lidas do CSV
SELECT COUNT(*) AS aluno_origem FROM stg_aluno;
\gset
\echo 'Total de linhas em ALUNO.csv (staging): ' :aluno_origem

-- Inserir TODOS os alunos sem DISTINCT ON
INSERT INTO aluno (
  id_aluno_graduacao,
  id_curso,
  raca_cor,
  sexo,
  ano_nascimento,
  ensino_medio,
  cidade_origem,
  estado_origem,
  pais_origem,
  cotas,
  tipo_ingresso,
  forma_ingresso,
  ano_matricula,
  situacao,
  motivo_desvinculo,
  data_desvinculo,
  cr,
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
SELECT
  NULLIF(BTRIM(id_aluno_graduacao), '')::INTEGER,
  NULLIF(BTRIM(id_curso), '')::INTEGER,
  NULLIF(BTRIM(raca_cor), ''),
  NULLIF(BTRIM(sexo), ''),
  CAST(NULLIF(BTRIM(ano_nascimento), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(ensino_medio), ''),
  NULLIF(BTRIM(cidade_origem), ''),
  NULLIF(BTRIM(estado_origem), ''),
  NULLIF(BTRIM(pais_origem), ''),
  NULLIF(BTRIM(cotas), ''),
  NULLIF(BTRIM(tipo_ingresso), ''),
  NULLIF(BTRIM(forma_ingresso), ''),
  CAST(NULLIF(BTRIM(ano_matricula), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(situacao), ''),
  NULLIF(BTRIM(motivo_desvinculo), ''),
  CASE
    WHEN NULLIF(BTRIM(data_desvinculo), '') ~ '^\d{2}/\d{2}/\d{4}$'
    THEN TO_TIMESTAMP(NULLIF(BTRIM(data_desvinculo), ''), 'DD/MM/YYYY')
    ELSE NULL
  END,
  CASE
    WHEN NULLIF(BTRIM(cr), '') ~ '^\d+(\.\d+)?$'
    THEN NULLIF(BTRIM(cr), '')::DECIMAL
    ELSE NULL
  END,
  NULLIF(BTRIM(max_nota), '')::DECIMAL,
  NULLIF(BTRIM(min_nota), '')::DECIMAL,
  NULLIF(BTRIM(avg_nota), '')::DECIMAL,
  NULLIF(BTRIM(median_nota), '')::DECIMAL,
  CAST(NULLIF(BTRIM(unique_disciplinas), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(max_frequencia), '')::DECIMAL,
  NULLIF(BTRIM(min_frequencia), '')::DECIMAL,
  NULLIF(BTRIM(avg_frequencia), '')::DECIMAL,
  NULLIF(BTRIM(median_frequencia), '')::DECIMAL,
  CAST(NULLIF(BTRIM(idade_matricula), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(distancia_campus), '')::DECIMAL,
  NULLIF(BTRIM(perc_reprovacao), '')::DECIMAL,
  NULLIF(BTRIM(perc_exames), '')::DECIMAL
FROM stg_aluno
WHERE NULLIF(BTRIM(id_aluno_graduacao), '') IS NOT NULL
  AND NULLIF(BTRIM(id_curso), '') IS NOT NULL;

SELECT COUNT(*) AS aluno_inserido FROM aluno;
\gset
\echo 'Alunos inseridos: ' :aluno_inserido
SELECT (:aluno_origem::INT - :aluno_inserido::INT) AS aluno_diferenca;
\gset
\echo 'Diferença: ' :aluno_diferenca

INSERT INTO import_statistics (tabela, linhas_origem, linhas_inseridas, linhas_descartadas)
VALUES ('ALUNO', :aluno_origem::INT, :aluno_inserido::INT, :aluno_diferenca::INT);

\echo '== Importando DISCIPLINA.csv (SEM DISTINCT) =='
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

SELECT COUNT(*) AS disciplina_origem FROM stg_disciplina;
\gset
\echo 'Total de linhas em DISCIPLINA.csv (staging): ' :disciplina_origem

-- Inserir disciplinas ÚNICAS
-- Aqui SIM fazemos DISTINCT porque são as disciplinas que o sistema oferece
INSERT INTO disciplina (
  id_disciplina,
  id_curso,
  nome_disciplina,
  nome_disciplina_normalizado
)
SELECT DISTINCT
  NULLIF(BTRIM(id_disciplina), '')::NUMERIC::INTEGER,
  NULLIF(BTRIM(id_curso), '')::NUMERIC::INTEGER,
  NULLIF(BTRIM(nome_disciplina), ''),
  lower(trim(regexp_replace(unaccent(NULLIF(BTRIM(nome_disciplina), '')), '[[:space:]]+', ' ', 'g')))
FROM stg_disciplina
WHERE NULLIF(BTRIM(id_disciplina), '') IS NOT NULL
  AND NULLIF(BTRIM(id_curso), '') IS NOT NULL
  AND NULLIF(BTRIM(nome_disciplina), '') IS NOT NULL;

SELECT COUNT(*) AS disciplina_inserida FROM disciplina;
\gset
\echo 'Disciplinas únicas inseridas: ' :disciplina_inserida

-- Importar ALUNO_DISCIPLINA COM LOGGING de dados órfãos
-- IMPORTANTE: Usar LEFT JOINs para identificar dados órfãos
DROP TABLE IF EXISTS stg_aluno_disciplina_parsed;
CREATE TEMP TABLE stg_aluno_disciplina_parsed AS
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
  AND NULLIF(BTRIM(id_disciplina), '') IS NOT NULL;

-- Registrar dados ÓRFÃOS (alunos que não existem)
INSERT INTO dados_descartados_log (tabela_origem, id_original_texto, motivo_descarte, valor_descartado)
SELECT 
  'ALUNO_DISCIPLINA',
  CAST(adp.id_aluno_graduacao_int AS TEXT),
  'Aluno não encontrado na tabela ALUNO',
  'ID Aluno: ' || adp.id_aluno_graduacao_int || ' | ID Disciplina: ' || adp.id_disciplina_int
FROM stg_aluno_disciplina_parsed adp
LEFT JOIN aluno a ON a.id_aluno_graduacao = adp.id_aluno_graduacao_int
WHERE a.id_aluno_graduacao IS NULL;

-- Registrar dados ÓRFÃOS (disciplinas que não existem)
INSERT INTO dados_descartados_log (tabela_origem, id_original_texto, motivo_descarte, valor_descartado)
SELECT 
  'ALUNO_DISCIPLINA',
  CAST(adp.id_disciplina_int AS TEXT),
  'Disciplina não encontrada na tabela DISCIPLINA',
  'ID Disciplina: ' || adp.id_disciplina_int || ' | ID Aluno: ' || adp.id_aluno_graduacao_int
FROM stg_aluno_disciplina_parsed adp
LEFT JOIN disciplina d ON d.id_disciplina = adp.id_disciplina_int
WHERE d.id_disciplina IS NULL;

-- Inserir APENAS registros válidos (que têm aluno E disciplina)
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
  adp.id_aluno_graduacao_int,
  adp.id_disciplina_int,
  adp.conceito_val,
  adp.frequencia_val,
  adp.tipo_efetivacao_val,
  adp.tipo_nota_val,
  adp.nota_val
FROM stg_aluno_disciplina_parsed adp
JOIN aluno a ON a.id_aluno_graduacao = adp.id_aluno_graduacao_int
JOIN disciplina d ON d.id_disciplina = adp.id_disciplina_int;

SELECT COUNT(*) AS aluno_disciplina_inserida FROM aluno_disciplina;
\gset
SELECT COUNT(*) AS aluno_disciplina_descartada FROM dados_descartados_log WHERE tabela_origem = 'ALUNO_DISCIPLINA';
\gset
\echo 'Registros ALUNO_DISCIPLINA inseridos: ' :aluno_disciplina_inserida
\echo 'Registros ALUNO_DISCIPLINA descartados: ' :aluno_disciplina_descartada

INSERT INTO import_statistics (tabela, linhas_origem, linhas_inseridas, linhas_descartadas)
SELECT 'ALUNO_DISCIPLINA', 
  (SELECT COUNT(*) FROM stg_aluno_disciplina_parsed),
  :aluno_disciplina_inserida::INT,
  :aluno_disciplina_descartada::INT;

\echo '== Importando OUTPUT_MODELO.csv =='
DROP TABLE IF EXISTS stg_output_modelo;
CREATE TEMP TABLE stg_output_modelo (
  id_aluno_graduacao TEXT,
  classificacao TEXT
);
\copy stg_output_modelo FROM '/csvdata/OUTPUT_MODELO.csv' DELIMITER ',' CSV HEADER;

SELECT COUNT(*) AS output_modelo_origem FROM stg_output_modelo;
\gset

-- Registrar dados órfãos
INSERT INTO dados_descartados_log (tabela_origem, id_original_texto, motivo_descarte)
SELECT 
  'OUTPUT_MODELO',
  CAST(CAST(NULLIF(BTRIM(som.id_aluno_graduacao), '') AS DECIMAL)::INTEGER AS TEXT),
  'Aluno não encontrado em ALUNO'
FROM stg_output_modelo som
LEFT JOIN aluno a 
  ON a.id_aluno_graduacao = CAST(NULLIF(BTRIM(som.id_aluno_graduacao), '') AS DECIMAL)::INTEGER
WHERE NULLIF(BTRIM(som.id_aluno_graduacao), '') IS NOT NULL
  AND a.id_aluno_graduacao IS NULL;

INSERT INTO output_modelo (id_aluno_graduacao, classificacao)
SELECT
  CAST(NULLIF(BTRIM(som.id_aluno_graduacao), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(som.classificacao), '')::DECIMAL
FROM stg_output_modelo som
JOIN aluno a 
  ON a.id_aluno_graduacao = CAST(NULLIF(BTRIM(som.id_aluno_graduacao), '') AS DECIMAL)::INTEGER
WHERE NULLIF(BTRIM(som.id_aluno_graduacao), '') IS NOT NULL;

SELECT COUNT(*) AS output_modelo_inserida FROM output_modelo;
\gset
SELECT COUNT(*) AS output_modelo_descartada FROM dados_descartados_log WHERE tabela_origem = 'OUTPUT_MODELO';
\gset
\echo 'OUTPUT_MODELO inseridos: ' :output_modelo_inserida
\echo 'OUTPUT_MODELO descartados: ' :output_modelo_descartada

INSERT INTO import_statistics (tabela, linhas_origem, linhas_inseridas, linhas_descartadas)
VALUES ('OUTPUT_MODELO', :output_modelo_origem::INT, :output_modelo_inserida::INT, :output_modelo_descartada::INT);

\echo '== Importando PESO_FEATURES.csv =='
DROP TABLE IF EXISTS stg_peso_features;
CREATE TEMP TABLE stg_peso_features (
  id_aluno_graduacao TEXT,
  feature TEXT,
  peso TEXT,
  descricao TEXT
);
\copy stg_peso_features FROM '/csvdata/PESO_FEATURES.csv' DELIMITER ',' CSV HEADER;

SELECT COUNT(*) AS peso_features_origem FROM stg_peso_features;
\gset

-- Registrar dados órfãos
INSERT INTO dados_descartados_log (tabela_origem, id_original_texto, motivo_descarte)
SELECT 
  'PESO_FEATURES',
  CAST(CAST(NULLIF(BTRIM(spf.id_aluno_graduacao), '') AS DECIMAL)::INTEGER AS TEXT),
  'Aluno não encontrado em ALUNO'
FROM stg_peso_features spf
LEFT JOIN aluno a 
  ON a.id_aluno_graduacao = CAST(NULLIF(BTRIM(spf.id_aluno_graduacao), '') AS DECIMAL)::INTEGER
WHERE NULLIF(BTRIM(spf.id_aluno_graduacao), '') IS NOT NULL
  AND a.id_aluno_graduacao IS NULL;

INSERT INTO peso_features (id_aluno_graduacao, feature, peso, descricao)
SELECT
  CAST(NULLIF(BTRIM(spf.id_aluno_graduacao), '') AS DECIMAL)::INTEGER,
  NULLIF(BTRIM(spf.feature), ''),
  NULLIF(BTRIM(spf.peso), '')::DECIMAL,
  NULLIF(BTRIM(spf.descricao), '')
FROM stg_peso_features spf
JOIN aluno a 
  ON a.id_aluno_graduacao = CAST(NULLIF(BTRIM(spf.id_aluno_graduacao), '') AS DECIMAL)::INTEGER
WHERE NULLIF(BTRIM(spf.id_aluno_graduacao), '') IS NOT NULL
  AND NULLIF(BTRIM(spf.feature), '') IS NOT NULL;

SELECT COUNT(*) AS peso_features_inserida FROM peso_features;
\gset
SELECT COUNT(*) AS peso_features_descartada FROM dados_descartados_log WHERE tabela_origem = 'PESO_FEATURES';
\gset
\echo 'PESO_FEATURES inseridos: ' :peso_features_inserida
\echo 'PESO_FEATURES descartados: ' :peso_features_descartada

INSERT INTO import_statistics (tabela, linhas_origem, linhas_inseridas, linhas_descartadas)
VALUES ('PESO_FEATURES', :peso_features_origem::INT, :peso_features_inserida::INT, :peso_features_descartada::INT);

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
SELECT setval(pg_get_serial_sequence('import_statistics', 'id'), COALESCE((SELECT MAX(id) FROM import_statistics), 1), true);
SELECT setval(pg_get_serial_sequence('dados_descartados_log', 'id'), COALESCE((SELECT MAX(id) FROM dados_descartados_log), 1), true);

\echo '== Seed consistente de tipos de pró-reitoria =='
INSERT INTO tipo_proreitoria (nome_proreitoria)
VALUES
  ('Graduação'),
  ('Pesquisa'),
  ('Extensão');

\echo '== Seed consistente de usuários e vínculos (EXPANDIDO) =='
-- Script similar ao original, mas mais robusto
-- (mantém a lógica original de criação de usuários)
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
  v_aluno_3 INT;
  v_aluno_4 INT;

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
  v_aluno_user_2 INT;
  v_aluno_user_3 INT;
  v_aluno_user_4 INT;
  v_prof_pendente_user INT;
  v_dep_rejeitado_user INT;
BEGIN
    -- Base principal
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
  JOIN campus ca ON ca.id_campus = un.id_campus
  JOIN curso c ON c.id_unidade = un.id_unidade
  JOIN disciplina d ON d.id_curso = c.id_curso
  JOIN aluno a ON a.id_curso = c.id_curso
  ORDER BY ca.id_campus, un.id_unidade, c.id_curso, d.id_disciplina, a.id_aluno_graduacao
  LIMIT 1;

  -- Base secundária
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
  JOIN campus ca ON ca.id_campus = un.id_campus
  JOIN curso c ON c.id_unidade = un.id_unidade
  JOIN disciplina d ON d.id_curso = c.id_curso
  JOIN aluno a ON a.id_curso = c.id_curso
  WHERE ca.id_campus <> v_campus_1 OR un.id_unidade <> v_unidade_1
  ORDER BY ca.id_campus, un.id_unidade, c.id_curso, d.id_disciplina, a.id_aluno_graduacao
  LIMIT 1;

  -- Alunos adicionais para melhor representação
  SELECT a.id_aluno_graduacao INTO v_aluno_3
  FROM aluno a
  WHERE a.id_aluno_graduacao <> v_aluno_1 AND a.id_aluno_graduacao <> v_aluno_2
  ORDER BY a.id_aluno_graduacao
  LIMIT 1 OFFSET 2;

  SELECT a.id_aluno_graduacao INTO v_aluno_4
  FROM aluno a
  WHERE a.id_aluno_graduacao <> v_aluno_1 AND a.id_aluno_graduacao <> v_aluno_2 AND a.id_aluno_graduacao <> COALESCE(v_aluno_3, 0)
  ORDER BY a.id_aluno_graduacao
  LIMIT 1 OFFSET 3;

  -- Fallbacks
  IF v_campus_2 IS NULL THEN v_campus_2 := v_campus_1; END IF;
  IF v_unidade_2 IS NULL THEN v_unidade_2 := v_unidade_1; END IF;
  IF v_curso_2 IS NULL THEN v_curso_2 := v_curso_1; END IF;
  IF v_disciplina_2 IS NULL THEN v_disciplina_2 := v_disciplina_1; END IF;
  IF v_aluno_2 IS NULL THEN v_aluno_2 := v_aluno_1; END IF;
  IF v_aluno_3 IS NULL THEN v_aluno_3 := v_aluno_1; END IF;
  IF v_aluno_4 IS NULL THEN v_aluno_4 := v_aluno_2; END IF;

  SELECT id_departamento INTO v_departamento_1
  FROM departamento WHERE id_unidade = v_unidade_1 ORDER BY id_departamento LIMIT 1;

  IF v_departamento_1 IS NULL THEN
    SELECT id_departamento, id_unidade INTO v_departamento_1, v_unidade_1
    FROM departamento ORDER BY id_departamento LIMIT 1;
  END IF;

  SELECT id_departamento INTO v_departamento_2
  FROM departamento
  WHERE id_unidade = v_unidade_2 AND id_departamento <> v_departamento_1
  ORDER BY id_departamento LIMIT 1;

  IF v_departamento_2 IS NULL THEN
    SELECT id_departamento INTO v_departamento_2
    FROM departamento WHERE id_departamento <> v_departamento_1
    ORDER BY id_departamento LIMIT 1;
  END IF;

  IF v_departamento_2 IS NULL THEN v_departamento_2 := v_departamento_1; END IF;

  IF v_campus_1 IS NULL OR v_unidade_1 IS NULL OR v_curso_1 IS NULL OR v_disciplina_1 IS NULL OR v_aluno_1 IS NULL THEN
    RAISE EXCEPTION 'Dados-base insuficientes. Verifique a interseção entre UNIDADE, CURSO, DISCIPLINA e ALUNO.';
  END IF;

  -- Obter categorias
  SELECT id_categoria_usuario INTO v_cat_admin FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%admin%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_reitoria FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%reitor%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_proreitoria FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%pro%reitor%' OR lower(trim(nome_categoria)) LIKE '%pró%reitor%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_dep FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%depart%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_coord FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%coord%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_prof FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%prof%' ORDER BY id_categoria_usuario LIMIT 1;
  SELECT id_categoria_usuario INTO v_cat_aluno FROM categoria_usuario WHERE lower(trim(nome_categoria)) LIKE '%aluno%' ORDER BY id_categoria_usuario LIMIT 1;

  IF v_cat_admin IS NULL OR v_cat_reitoria IS NULL OR v_cat_proreitoria IS NULL OR v_cat_dep IS NULL OR v_cat_coord IS NULL OR v_cat_prof IS NULL OR v_cat_aluno IS NULL THEN
    RAISE EXCEPTION 'Nem todas as categorias necessárias foram encontradas em CATEGORIA_USUARIO.csv';
  END IF;

  SELECT id_tipo_proreitoria INTO v_tipo_proreitoria_id FROM tipo_proreitoria ORDER BY id_tipo_proreitoria LIMIT 1;

  -- Criar usuários
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

  -- 4 Alunos aprovados para melhor teste
  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno Teste 1', 'aluno1.teste@unesp.br', '11111111117', '(11) 99999-0007', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_user;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_user, v_unidade_1, v_aluno_1);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno Teste 2', 'aluno2.teste@unesp.br', '11111111121', '(11) 99999-0011', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_user_2;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_user_2, v_unidade_1, v_aluno_2);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno Teste 3', 'aluno3.teste@unesp.br', '11111111122', '(11) 99999-0012', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_user_3;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_user_3, v_unidade_2, v_aluno_3);

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro, data_atualizacao)
  VALUES (v_cat_aluno, 'Aluno Teste 4', 'aluno4.teste@unesp.br', '11111111123', '(11) 99999-0013', 'APROVADO', CURRENT_TIMESTAMP)
  RETURNING id_usuario INTO v_aluno_user_4;
  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao) VALUES (v_aluno_user_4, v_unidade_2, v_aluno_4);

  -- Usuários com status pendente para teste
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

SELECT setval(pg_get_serial_sequence('tipo_proreitoria', 'id_tipo_proreitoria'), COALESCE((SELECT MAX(id_tipo_proreitoria) FROM tipo_proreitoria), 1), true);
SELECT setval(pg_get_serial_sequence('usuario', 'id_usuario'), COALESCE((SELECT MAX(id_usuario) FROM usuario), 1), true);
SELECT setval(pg_get_serial_sequence('documento_usuario', 'id_documento'), COALESCE((SELECT MAX(id_documento) FROM documento_usuario), 1), true);

\echo '========================================'
\echo '== RELATÓRIO FINAL DE IMPORTAÇÃO ========'
\echo '========================================'

SELECT 
  tabela,
  linhas_origem,
  linhas_inseridas,
  linhas_descartadas,
  CASE 
    WHEN linhas_origem > 0 THEN ROUND(100.0 * linhas_inseridas / linhas_origem, 2)
    ELSE 0
  END as percentual_inserido
FROM import_statistics
ORDER BY tabela;

\echo '';
\echo 'Resumo de dados descartados:';
SELECT 
  tabela_origem,
  COUNT(*) as quantidade,
  COUNT(DISTINCT motivo_descarte) as motivos_distintos
FROM dados_descartados_log
GROUP BY tabela_origem;

\echo '';
\echo '== Conferência rápida de integridade =='
SELECT 'campus' AS tabela, COUNT(*) AS qtd FROM campus;
SELECT 'unidade' AS tabela, COUNT(*) AS qtd FROM unidade;
SELECT 'categoria_usuario' AS tabela, COUNT(*) AS qtd FROM categoria_usuario;
SELECT 'departamento' AS tabela, COUNT(*) AS qtd FROM departamento;
SELECT 'periodo' AS tabela, COUNT(*) AS qtd FROM periodo;
SELECT 'curso' AS tabela, COUNT(*) AS qtd FROM curso;
SELECT 'disciplina' AS tabela, COUNT(*) AS qtd FROM disciplina;
SELECT 'aluno' AS tabela, COUNT(*) AS qtd FROM aluno;
SELECT 'aluno_disciplina' AS tabela, COUNT(*) AS qtd FROM aluno_disciplina;
SELECT 'output_modelo' AS tabela, COUNT(*) AS qtd FROM output_modelo;
SELECT 'peso_features' AS tabela, COUNT(*) AS qtd FROM peso_features;
SELECT 'usuario' AS tabela, COUNT(*) AS qtd FROM usuario;
SELECT 'documento_usuario' AS tabela, COUNT(*) AS qtd FROM documento_usuario;

\echo '';
\echo 'Alunos por campus:';
SELECT 
  ca.nome_campus,
  COUNT(DISTINCT a.id_aluno_graduacao) as qtd_alunos
FROM aluno a
JOIN curso c ON a.id_curso = c.id_curso
JOIN unidade un ON c.id_unidade = un.id_unidade
JOIN campus ca ON un.id_campus = ca.id_campus
GROUP BY ca.id_campus, ca.nome_campus
ORDER BY qtd_alunos DESC;

\echo '';
\echo '✅ Importação concluída!';
INSERT INTO import_status (chave, valor, atualizado_em)
VALUES ('seed_status', 'done', CURRENT_TIMESTAMP)
ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor, atualizado_em = EXCLUDED.atualizado_em;