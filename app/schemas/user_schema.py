from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Union, Annotated, Optional
from typing_extensions import Literal
from enum import Enum
import re
from pathlib import Path
from fastapi import Form

class CategoriaEnum(str, Enum):
    ALUNO = "ALUNO"
    PROFESSOR = "PROFESSOR"
    COORDENACAO = "COORDENAÇÃO"
    DEPARTAMENTO = "DEPARTAMENTO"
    PRO_REITORIA = "PRO-REITORIA"
    REITORIA = "REITORIA"
    ADMIN = "ADMIN"

class UserBase(BaseModel):
    nome: str = Field(..., description="Name of the user")
    email: EmailStr = Field(..., description="Institutional email of the user")
    cpf: str = Field(..., description="CPF of the user")
    telefone: str = Field(..., description="Phone number of the user, with only de DDD and number, with the format (xx) xxxxx-xxxx or (xx) xxxx-xxxx")

    @field_validator("email")
    @classmethod
    def validate_instituional_email(cls, value: EmailStr):
        if not value.endswith("@unesp.br"):
            raise ValueError("Email must be an institutional email")
        return value

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str):
        cpf = re.sub(r"\D", "", value)

        if len(cpf) != 11:
            raise ValueError("CPF must contain 11 digits")

        if cpf == cpf[0] * 11:
            raise ValueError("Invalid CPF")

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        digito1 = 0 if digito1 == 10 else digito1

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        digito2 = 0 if digito2 == 10 else digito2

        if cpf[-2:] != f"{digito1}{digito2}":
            raise ValueError("Invalid CPF")

        return value
    
    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, value: str):
        pattern = r"^\(\d{2}\)\s?\d{4,5}-\d{4}$"
        if not re.match(pattern, value):
            raise ValueError(
                "Phone number must be in the format (xx) xxxx-xxxx or (xx) xxxxx-xxxx"
            )
        return value
        

class UserAdmin(UserBase):
    categoria: Literal[CategoriaEnum.ADMIN]
    pass

class UserReitor(UserBase):
    categoria: Literal[CategoriaEnum.REITORIA]
    campus_id: int = Field(..., description="Unique identifier for a 'campus' already registered on the system")
    pass

class UserProReitor(UserReitor):
    categoria: Literal[CategoriaEnum.PRO_REITORIA]
    proreitoria_id: int = Field(..., description="Unique identifier for a 'tipo_proreitoria' already registered on the system")

class UserDepartamento(UserBase):
    categoria: Literal[CategoriaEnum.DEPARTAMENTO]
    unidade_id: int = Field(..., description="Unique identifier for a 'unidade' already registered on the system")
    departamento_id: int = Field(..., description="Unique identifier for a 'departamento' already registered on the system")

class UserCoordenacao(UserBase):
    categoria: Literal[CategoriaEnum.COORDENACAO]
    unidade_id: int = Field(..., description="Unique identifier for a 'unidade' already registered on the system")
    curso_id: int = Field(..., description="Unique identifier for a 'curso' already registered on the system")

class UserProfessor(UserCoordenacao):
    categoria: Literal[CategoriaEnum.PROFESSOR]
    unidade_id: int = Field(..., description="Unique identifier for a 'unidade' already registered on the system")
    disciplinas: List[int] = Field(..., description="List of 'disciplinas' ids")

class UserAluno(UserBase):
    categoria: Literal[CategoriaEnum.ALUNO]
    unidade_id: int = Field(..., description="Unique identifier for a 'unidade' already registered on the system")
    ra: str = Field(..., description="RA of the user")

    @field_validator("ra")
    @classmethod
    def validate_ra(cls, value: str):
        if not value.isdigit():
            raise ValueError("RA must contain only digits")
        return value

UserCreate = Annotated[
    Union[
        UserAluno,
        UserProfessor,
        UserCoordenacao,
        UserDepartamento,
        UserReitor,
        UserProReitor,
        UserAdmin
    ],
    Field(discriminator="categoria")
]

class UserCreateForm:
    def __init__(
        self,
        nome: str,
        email: EmailStr,
        cpf: str,
        telefone: str,
        categoria: CategoriaEnum,
        ra: Optional[str] = None,
        departamento_id: Optional[int] = None,
        curso_id: Optional[int] = None,
        disciplinas: Optional[List[int]] = None,
        unidade_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        proreitoria_id: Optional[int] = None
    ):
        self.nome = nome
        self.email = email
        self.cpf = cpf
        self.telefone = telefone
        self.categoria = categoria
        self.ra = ra
        self.departamento_id = departamento_id
        self.curso_id = curso_id
        self.disciplinas = disciplinas
        self.unidade_id = unidade_id
        self.campus_id = campus_id
        self.proreitoria_id = proreitoria_id

    @classmethod
    def as_form(
        cls,
        nome: str = Form(...),
        email: EmailStr = Form(...),
        cpf: str = Form(...),
        telefone: str = Form(...),
        categoria: CategoriaEnum = Form(...),

        ra: Optional[str] = Form(None),
        departamento_id: Optional[int] = Form(None),
        curso_id: Optional[int] = Form(None),
        disciplinas: List[int] = Form([]),
        unidade_id: Optional[int] = Form(None),
        campus_id: Optional[int] = Form(None),
        proreitoria_id: Optional[int] = Form(None)
    ):
        return cls(
            nome=nome,
            email=email,
            cpf=cpf,
            telefone=telefone,
            categoria=categoria,
            ra=ra,
            departamento_id=departamento_id,
            curso_id=curso_id,
            disciplinas=disciplinas,
            unidade_id=unidade_id,
            campus_id=campus_id,
            proreitoria_id=proreitoria_id
        )

class UserCreateResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for user")
    email: EmailStr = Field(..., description="Institutional email of the user")
    status: str = Field(..., description="User registration status")

class SavedFile(BaseModel):
    filename: str
    size: int
    mime_type: str
    base_path: Path

class UserCreationError(Exception):
    pass

class DisciplinaNotFoundError(UserCreationError):
    pass

class DuplicatedDisciplinaError(UserCreationError):
    pass

class CursoNotFoundError(UserCreationError):
    pass

class DepartamentoNotFoundError(UserCreationError):
    pass

class CategoriaNotFoundError(UserCreationError):
    pass

class CampusNotFoundError(UserCreationError):
    pass

class TipoProreitoriaNotFoundError(UserCreationError):
    pass

class UnidadeNotFoundError(UserCreationError):
    pass

class AlunoNotFoundError(UserCreationError):
    pass