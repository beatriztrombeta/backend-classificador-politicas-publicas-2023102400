from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, DECIMAL
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
from enum import Enum

class StatusCadastroEnum(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"

class StatusAnaliseEnum(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"

class User(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    id_categoria_usuario = Column(Integer, ForeignKey("categoria_usuario.id_categoria_usuario"), nullable=False)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String)
    telefone = Column(String)
    status_cadastro = Column(
        SQLEnum(
            StatusCadastroEnum,
            name="status_cadastro_enum",
            native_enum=True,
            create_type=False
        ),
        nullable=False
    )
    data_cadastro = Column(TIMESTAMP)
    data_atualizacao = Column(TIMESTAMP)

class UserCategory(Base):
    __tablename__ = "categoria_usuario"

    id_categoria_usuario = Column(Integer, primary_key=True, index=True)
    nome_categoria = Column(String, nullable=False)

class Campus(Base):
    __tablename__ = "campus"

    id_campus = Column(Integer, primary_key=True, index=True)
    nome_campus = Column(String, nullable=False)

class Unidade(Base):
    __tablename__ = "unidade"

    id_unidade = Column(Integer, primary_key=True, index=True)
    id_campus = Column(Integer, ForeignKey("campus.id_campus"), nullable=False)
    nome_unidade = Column(String, nullable=False)

class Periodo(Base):
    __tablename__ = "periodo"

    id_periodo = Column(Integer, primary_key=True, nullable=False)
    periodo = Column(String, nullable=False)


class Curso(Base):
    __tablename__ = "curso"

    id_curso = Column(Integer, primary_key=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodo.id_periodo"), nullable=False)
    nome_curso = Column(String, nullable=False)
    modalidade = Column(String)


class Departamento(Base):
    __tablename__ = "departamento"

    id_departamento = Column(Integer, primary_key=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    nome_departamento = Column(String, nullable=False)


class Disciplina(Base):
    __tablename__ = "disciplina"

    id_disciplina = Column(Integer, primary_key=True, index=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), nullable=False)
    nome_disciplina = Column(String, nullable=False)


class TipoProreitoria(Base):
    __tablename__ = "tipo_proreitoria"

    id_tipo_proreitoria = Column(Integer, primary_key=True, index=True)
    nome_proreitoria = Column(String, nullable=False)


class DocumentoUsuario(Base):
    __tablename__ = "documento_usuario"

    id_documento = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    tipo_documento = Column(String, nullable=False)
    storage_provider = Column(String, nullable=False)
    storage_bucket = Column(String)
    storage_key = Column(String, nullable=False)
    hash_arquivo = Column(String, nullable=False)
    mime_type = Column(String)
    tamanho_arquivo = Column(Integer)
    data_envio = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
    )
    status_analise = Column(
        SQLEnum(
            StatusAnaliseEnum,
            name="status_analise_enum",
            native_enum=True,
            create_type=False
        ),
        nullable=False
    )

class UserReitor(Base):
    __tablename__ = "usuario_reitor"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_campus = Column(Integer, ForeignKey("campus.id_campus"), primary_key=True)

class UserProrei(Base):
    __tablename__ = "usuario_prorei"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_proreitoria = Column(Integer, ForeignKey("tipo_proreitoria.id_tipo_proreitoria"), primary_key=True)
    id_campus = Column(Integer, ForeignKey("campus.id_campus"), nullable=False)

class UserAluno(Base):
    __tablename__ = "usuario_aluno"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_aluno_graduacao = Column(Integer, ForeignKey("aluno.id_aluno_graduacao"), primary_key=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)

class UserProfessor(Base):
    __tablename__ = "usuario_professor"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_disciplina = Column(Integer, ForeignKey("disciplina.id_disciplina"), primary_key=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)

class UserCoordenador(Base):
    __tablename__ = "usuario_coordenador"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), primary_key=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)

class UserDepartamento(Base):
    __tablename__ = "usuario_departamento"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_departamento = Column(Integer, ForeignKey("departamento.id_departamento"), primary_key=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)

class Aluno(Base):
    __tablename__ = "aluno"
    
    id_aluno_graduacao = Column(Integer, primary_key=True)
    id_curso = Column(String, ForeignKey("curso.id_curso"), nullable=False)
    raca_cor = Column(String)
    sexo = Column(String)
    ano_nascimento = Column(Integer)
    ensino_medio = Column(String)
    cidade_origem = Column(String)
    estado_origem = Column(String)
    pais_origem = Column(String)
    cotas = Column(String)
    tipo_ingresso = Column(String)
    forma_ingresso = Column(String)
    ano_matricula = Column(Integer)
    situacao = Column(String)
    motivo_desvinculo = Column(String)
    data_desvinculo = Column(TIMESTAMP)
    cr = Column(DECIMAL)
    max_nota = Column(DECIMAL)
    min_nota = Column(DECIMAL)
    avg_nota = Column(DECIMAL)
    median_nota = Column(DECIMAL)
    unique_disciplinas = Column(Integer)
    max_frequencia = Column(DECIMAL)
    min_frequencia = Column(DECIMAL)
    avg_frequencia = Column(DECIMAL)
    median_frequencia = Column(DECIMAL)
    idade_matricula = Column(Integer)
    perc_reprovacao = Column(DECIMAL)
    perc_exames = Column(DECIMAL)
    distancia_campus = Column(DECIMAL)