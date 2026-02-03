from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

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
    status_cadastro = Column(String, nullable=False)
    data_cadastro = Column(TIMESTAMP)
    data_atualizacao = Column(TIMESTAMP)
