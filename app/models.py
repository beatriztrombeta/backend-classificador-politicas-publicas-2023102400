from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

class StatusCadastroEnum(str, Enum):
    PENDENTE='PENDENTE'
    APROVADO='APROVADO'
    REJEITADO='REJEITADO'

Base = declarative_base()

class User(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    id_perfil = Column(Integer, ForeignKey("perfil_usuario.id_perfil"), nullable=False)
    id_campus = Column(Integer, ForeignKey("campus.id_campus"))
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))

    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String)
    telefone = Column(String)
    status_cadastro = Column(
        SQLEnum(
            StatusCadastroEnum,
            name="status_cadastro_enum",  # MESMO nome do enum no Postgres
            native_enum=True,
            create_type=False              # importante, pq o enum já existe
        ),
        nullable=False
    )
    data_cadastro = Column(TIMESTAMP)
    data_atualizacao = Column(TIMESTAMP)

class UserProfile(Base):
    __tablename__ = "perfil_usuario"

    id_perfil = Column(Integer, primary_key=True, index=True)
    nome_perfil = Column(String, nullable=False)
    descricao = Column(String)

class Campus(Base):
    __tablename__ = "campus"

    id_campus = Column(Integer, primary_key=True, index=True)
    nome_campus = Column(String, nullable=False)

class Unidade(Base):
    __tablename__ = "unidade"

    id_unidade = Column(Integer, primary_key=True, index=True)
    id_campus = Column(Integer, ForeignKey("campus.id_campus"), nullable=False)
    nome_unidade = Column(String, nullable=False)

class UserAluno(Base):
    __tablename__ = "usuario_aluno"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_aluno_graduacao = Column(Integer, ForeignKey("aluno.id_aluno_graduacao"), primary_key=True)

class UserProfessor(Base):
    __tablename__ = "usuario_professor"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), primary_key=True)

class UserCoordenador(Base):
    __tablename__ = "usuario_coordenador"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), primary_key=True)

class UserDepartamento(Base):
    __tablename__ = "usuario_departamento"

    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_departamento = Column(Integer, ForeignKey("departamento.id_departamento"), primary_key=True)

class Curso(Base):
    __tablename__ = "curso"

    id_curso = Column(Integer, primary_key=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodo.id_periodo"), nullable=False)
    nome_curso = Column(String, nullable=False)
    modalidade = Column(String)

class Periodo(Base):
    __tablename__ = "periodo"

    id_periodo = Column(Integer, primary_key=True, nullable=False)
    periodo = Column(String, nullable=False)

class Departamento(Base):
    __tablename__ = "departamento"

    id_departamento = Column(Integer, primary_key=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    nome_departamento = Column(String, nullable=False)