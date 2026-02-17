\set ON_ERROR_STOP on
\echo '== Importando CSVs (CAMPUS, UNIDADE, CATEGORIA_USUARIO, DEPARTAMENTO, PERIODO, CURSO) =='

\copy CAMPUS FROM '/csvdata/CAMPUS.csv' DELIMITER ',' CSV HEADER;
\copy UNIDADE FROM '/csvdata/UNIDADE.csv' DELIMITER ',' CSV HEADER;
\copy CATEGORIA_USUARIO FROM '/csvdata/CATEGORIA_USUARIO.csv' DELIMITER ',' CSV HEADER;
\copy DEPARTAMENTO FROM '/csvdata/DEPARTAMENTO.csv' DELIMITER ',' CSV HEADER;
\copy PERIODO FROM '/csvdata/PERIODO.csv' DELIMITER ',' CSV HEADER;
\copy CURSO FROM '/csvdata/CURSO.csv' DELIMITER ',' CSV HEADER;

\echo '== Seed de usuários/vínculos (RBAC) =='

DO $$
DECLARE
  v_campus_id INT;
  v_unidade_id INT;
  v_departamento_id INT;
  v_curso_id INT;
  v_periodo_id INT;

  v_tipo_proreitoria_id INT;

  v_disciplina_id INT;
  v_aluno_id INT;

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

BEGIN
  SELECT id_campus INTO v_campus_id FROM campus ORDER BY id_campus LIMIT 1;
  IF v_campus_id IS NULL THEN
    RAISE EXCEPTION 'Tabela CAMPUS está vazia. Importe CAMPUS.csv primeiro.';
  END IF;

  SELECT id_unidade INTO v_unidade_id FROM unidade WHERE id_campus = v_campus_id ORDER BY id_unidade LIMIT 1;
  IF v_unidade_id IS NULL THEN
    SELECT id_unidade INTO v_unidade_id FROM unidade ORDER BY id_unidade LIMIT 1;
  END IF;

  SELECT id_departamento INTO v_departamento_id
  FROM departamento
  WHERE id_unidade = v_unidade_id
  ORDER BY id_departamento
  LIMIT 1;

  IF v_departamento_id IS NULL THEN
    SELECT id_departamento, id_unidade INTO v_departamento_id, v_unidade_id
    FROM departamento
    ORDER BY id_departamento
    LIMIT 1;
  END IF;

  SELECT id_curso, id_periodo INTO v_curso_id, v_periodo_id
  FROM curso
  WHERE id_unidade = v_unidade_id
  ORDER BY id_curso
  LIMIT 1;

  IF v_curso_id IS NULL THEN
    SELECT id_curso, id_unidade, id_periodo INTO v_curso_id, v_unidade_id, v_periodo_id
    FROM curso ORDER BY id_curso LIMIT 1;
  END IF;

  IF v_periodo_id IS NULL THEN
    SELECT id_periodo INTO v_periodo_id FROM periodo ORDER BY id_periodo LIMIT 1;
  END IF;

  SELECT id_categoria_usuario INTO v_cat_admin
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%admin%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_admin IS NULL THEN RAISE EXCEPTION 'Categoria ADMIN não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_reitoria
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%reitor%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_reitoria IS NULL THEN RAISE EXCEPTION 'Categoria REITORIA não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_proreitoria
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%pro%reitor%'
     OR lower(nome_categoria) LIKE '%pró%reitor%'
     OR lower(nome_categoria) LIKE '%proreitor%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_proreitoria IS NULL THEN RAISE EXCEPTION 'Categoria PRÓ-REITORIA não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_dep
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%depart%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_dep IS NULL THEN RAISE EXCEPTION 'Categoria DEPARTAMENTO não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_coord
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%coord%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_coord IS NULL THEN RAISE EXCEPTION 'Categoria COORDENAÇÃO não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_prof
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%prof%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_prof IS NULL THEN RAISE EXCEPTION 'Categoria PROFESSOR não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_categoria_usuario INTO v_cat_aluno
  FROM categoria_usuario
  WHERE lower(nome_categoria) LIKE '%aluno%'
  ORDER BY id_categoria_usuario LIMIT 1;
  IF v_cat_aluno IS NULL THEN RAISE EXCEPTION 'Categoria ALUNO não encontrada em CATEGORIA_USUARIO.'; END IF;

  SELECT id_tipo_proreitoria INTO v_tipo_proreitoria_id
  FROM tipo_proreitoria
  ORDER BY id_tipo_proreitoria
  LIMIT 1;

  IF v_tipo_proreitoria_id IS NULL THEN
    INSERT INTO tipo_proreitoria (nome_proreitoria)
    VALUES ('Graduação')
    RETURNING id_tipo_proreitoria INTO v_tipo_proreitoria_id;
  END IF;

  SELECT id_disciplina INTO v_disciplina_id
  FROM disciplina
  WHERE id_curso = v_curso_id
  ORDER BY id_disciplina
  LIMIT 1;

  IF v_disciplina_id IS NULL THEN
    INSERT INTO disciplina (id_curso, nome_disciplina)
    VALUES (v_curso_id, 'DISCIPLINA TESTE - RBAC')
    RETURNING id_disciplina INTO v_disciplina_id;
  END IF;

  SELECT id_aluno_graduacao INTO v_aluno_id
  FROM aluno
  WHERE id_curso = v_curso_id
  ORDER BY id_aluno_graduacao
  LIMIT 1;

  IF v_aluno_id IS NULL THEN
    INSERT INTO aluno (id_curso, ano_matricula, situacao)
    VALUES (v_curso_id, EXTRACT(YEAR FROM NOW())::INT, 'ATIVO')
    RETURNING id_aluno_graduacao INTO v_aluno_id;

    INSERT INTO output_modelo (id_aluno_graduacao, classificacao)
    VALUES (v_aluno_id, 0.50)
    ON CONFLICT (id_aluno_graduacao) DO NOTHING;
  END IF;

  INSERT INTO aluno_disciplina (id_aluno_graduacao, id_disciplina, conceito, frequencia, nota)
  VALUES (v_aluno_id, v_disciplina_id, 'A', 0.90, 8.5)
  ON CONFLICT (id_aluno_graduacao, id_disciplina) DO NOTHING;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_admin, 'Admin Teste', 'admin.teste@exemplo.com', '00000000001', '11999990001', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_admin_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_reitoria, 'Reitoria Teste', 'reitoria.teste@exemplo.com', '00000000002', '11999990002', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_reitoria_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_proreitoria, 'Pro-Reitoria Teste', 'prorei.teste@exemplo.com', '00000000003', '11999990003', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_prorei_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_dep, 'Departamento Teste', 'dep.teste@exemplo.com', '00000000004', '11999990004', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_dep_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_coord, 'Coordenacao Teste', 'coord.teste@exemplo.com', '00000000005', '11999990005', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_coord_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_prof, 'Professor Teste', 'prof.teste@exemplo.com', '00000000006', '11999990006', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_prof_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, cpf, telefone, status_cadastro)
  VALUES (v_cat_aluno, 'Aluno Teste', 'aluno.teste@exemplo.com', '00000000007', '11999990007', 'APROVADO')
  ON CONFLICT (email) DO UPDATE SET id_categoria_usuario = EXCLUDED.id_categoria_usuario
  RETURNING id_usuario INTO v_aluno_user;

  INSERT INTO usuario (id_categoria_usuario, nome, email, status_cadastro)
  VALUES
    (v_cat_aluno, 'Pendente 1', 'pendente1@exemplo.com', 'PENDENTE'),
    (v_cat_aluno, 'Pendente 2', 'pendente2@exemplo.com', 'PENDENTE'),
    (v_cat_aluno, 'Pendente 3', 'pendente3@exemplo.com', 'PENDENTE')
  ON CONFLICT (email) DO NOTHING;

  INSERT INTO usuario_reitor (id_usuario, id_campus)
  VALUES (v_reitoria_user, v_campus_id)
  ON CONFLICT (id_usuario, id_campus) DO NOTHING;

  INSERT INTO usuario_prorei (id_usuario, id_campus, id_proreitoria)
  VALUES (v_prorei_user, v_campus_id, v_tipo_proreitoria_id)
  ON CONFLICT (id_usuario, id_proreitoria) DO NOTHING;

  INSERT INTO usuario_departamento (id_usuario, id_unidade, id_departamento)
  VALUES (v_dep_user, v_unidade_id, v_departamento_id)
  ON CONFLICT (id_usuario, id_departamento) DO NOTHING;

  INSERT INTO usuario_coordenador (id_usuario, id_unidade, id_curso)
  VALUES (v_coord_user, v_unidade_id, v_curso_id)
  ON CONFLICT (id_usuario, id_curso) DO NOTHING;

  INSERT INTO usuario_professor (id_usuario, id_unidade, id_disciplina)
  VALUES (v_prof_user, v_unidade_id, v_disciplina_id)
  ON CONFLICT (id_usuario, id_disciplina) DO NOTHING;

  INSERT INTO usuario_aluno (id_usuario, id_unidade, id_aluno_graduacao)
  VALUES (v_aluno_user, v_unidade_id, v_aluno_id)
  ON CONFLICT (id_usuario, id_aluno_graduacao) DO NOTHING;

  RAISE NOTICE 'Seed OK. Campus=% Unidade=% Curso=% Disciplina=% Aluno=%', v_campus_id, v_unidade_id, v_curso_id, v_disciplina_id, v_aluno_id;
  RAISE NOTICE 'Emails: admin.teste@exemplo.com | reitoria.teste@exemplo.com | prorei.teste@exemplo.com | dep.teste@exemplo.com | coord.teste@exemplo.com | prof.teste@exemplo.com | aluno.teste@exemplo.com';
END $$;

\echo '== Conferência rápida =='
SELECT 'CAMPUS' AS tabela, COUNT(*) AS qtd FROM campus;
SELECT 'UNIDADE' AS tabela, COUNT(*) AS qtd FROM unidade;
SELECT 'DEPARTAMENTO' AS tabela, COUNT(*) AS qtd FROM departamento;
SELECT 'PERIODO' AS tabela, COUNT(*) AS qtd FROM periodo;
SELECT 'CURSO' AS tabela, COUNT(*) AS qtd FROM curso;
SELECT 'USUARIO' AS tabela, COUNT(*) AS qtd FROM usuario;
