from fastapi import APIRouter, Form, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator, TypeAdapter
from typing import List, Union, Annotated, Optional
from typing_extensions import Literal
from enum import IntEnum
import re
from pathlib import Path
import os
import uuid
from app.models import User, UserProfile, StatusCadastroEnum
from sqlalchemy.orm import Session
from app.database import get_db

# TODO: Melhorar esse import
from app import models

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

class CategoriaEnum(IntEnum):
    ALUNO = 1
    PROFESSOR = 2
    COORDENACAO = 3
    DEPARTAMENTO = 4
    PRO_REITORIA = 5
    REITORIA = 6

class UserBase(BaseModel):
    nome: str = Field(..., description="Name of the user")
    email: EmailStr = Field(..., description="Institutional email of the user")
    cpf: str = Field(..., description="CPF of the user")
    telefone: str = Field(..., description="Phone number of the user, with only de DDD and number, with the format (xx) xxxxx-xxxx or (xx) xxxx-xxxx")
    campus_id: int = Field(..., description="Unique identifier for a 'campus' already registered on the system")

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
        

class UserReitor(UserBase):
    categoria: Literal[CategoriaEnum.REITORIA]
    pass

class UserProReitor(UserBase):
    categoria: Literal[CategoriaEnum.PRO_REITORIA]
    area_id: int = Field(..., description="lorem ipsum")

class UserDepartamento(UserBase):
    categoria: Literal[CategoriaEnum.DEPARTAMENTO]
    departamento_id: int = Field(..., description="Unique identifier for a 'departamento' already registered on the system")

class UserCoordenacao(UserBase):
    categoria: Literal[CategoriaEnum.COORDENACAO]
    curso_id: int = Field(..., description="Unique identifier for a 'curso' already registered on the system")

class UserProfessor(UserCoordenacao):
    categoria: Literal[CategoriaEnum.PROFESSOR]
    disciplinas: List[int] = Field(..., description="List of 'disciplinas' ids")

class UserAluno(UserBase):
    categoria: Literal[CategoriaEnum.ALUNO]
    ra: str = Field(..., min_length=9, max_length=9, description="RA of the user")

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
        UserProReitor
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
        campus_id: int,
        categoria: CategoriaEnum,
        ra: Optional[str] = None,
        area_id: Optional[int] = None,
        departamento_id: Optional[int] = None,
        curso_id: Optional[int] = None,
        disciplinas: Optional[List[int]] = None,
    ):
        self.nome = nome
        self.email = email
        self.cpf = cpf
        self.telefone = telefone
        self.campus_id = campus_id
        self.categoria = categoria
        self.ra = ra
        self.area_id = area_id
        self.departamento_id = departamento_id
        self.curso_id = curso_id
        self.disciplinas = disciplinas

    @classmethod
    def as_form(
        cls,
        nome: str = Form(...),
        email: EmailStr = Form(...),
        cpf: str = Form(...),
        telefone: str = Form(...),
        campus_id: int = Form(...),
        categoria: CategoriaEnum = Form(...),

        ra: Optional[str] = Form(None),
        area_id: Optional[int] = Form(None),
        departamento_id: Optional[int] = Form(None),
        curso_id: Optional[int] = Form(None),
        disciplinas: Optional[List[int]] = Form(None),
    ):
        return cls(
            nome,
            email,
            cpf,
            telefone,
            campus_id,
            categoria,
            ra,
            area_id,
            departamento_id,
            curso_id,
            disciplinas,
        )

async def validate_file(file: UploadFile) -> None:
    threshold = 5 * 1024 * 1024 # 5 MB
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Only pdf files are allowed")
    
    content = await file.read()

    if not content:
        raise HTTPException(422, "Empty pdf file")

    if not content.startswith(b"%PDF"):
        raise HTTPException(422, "This file is not a valid pdf")

    await file.seek(0)

    if file.size > threshold:
        raise HTTPException(status_code=422, detail="The file exceeds 5 MB.")

async def save_file(file: UploadFile) -> str:
    base_dir = Path(os.getenv("FILES_PATH"))
    base_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4()}{ext}"

    file_path = base_dir / filename

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return filename

def insert_user_profile(name: str, description: str, db: Session) -> UserProfile:
    profile = UserProfile(
        nome_perfil=name,
        descricao=description
    )
    
    db.add(profile)
    db.flush()

    return profile

def insert_base_user(new_user: UserBase, db: Session) -> User:
    profile = insert_user_profile(new_user.nome, description="", db=db)

    # TODO: Resgatar o id da unidade
    user = User(
            id_perfil=profile.id_perfil,
            nome=new_user.nome,
            email=new_user.email,
            cpf=new_user.cpf,
            telefone=new_user.telefone,
            status_cadastro=StatusCadastroEnum.PENDENTE,
            #id_campus=new_user.campus_id
        )
    
    db.add(user)
    db.flush()

    return user

def insert_usuario_aluno(new_user: UserAluno, db: Session) -> models.UserAluno:
    base_user = insert_base_user(new_user, db)
    
    # TODO: Adicionar o campo id_aluno_graduacao e talvez adicionar o campo RA no futuro
    user = models.UserAluno(
        id_usuario=base_user.id_usuario,
        #id_aluno_graduacao=new_user.ra
    )

    db.add(user)
    db.flush()

    return user

def insert_usuario_professor(new_user: UserProfessor, db: Session) -> models.UserProfessor:
    base_user = insert_base_user(new_user, db)

    # TODO: Adicionar o campo id_curso e talvez as disciplinas que o professor leciona
    user = models.UserProfessor(
        id_usuario=base_user.id_usuario,
        #id_curso=new_user.curso_id
    )

    db.add(user)
    db.flush()

    return user

def insert_usuario_coordenador(new_user: UserCoordenacao, db: Session) -> models.UserCoordenador:
    base_user = insert_base_user(new_user, db)

    # TODO: Adicionar o campo id_curso
    user = models.UserCoordenador(
        id_usuario=base_user.id_usuario,
        #id_curso=new_user.curso_id
    )

    db.add(user)
    db.flush()

    return user

def insert_usuario_departamento(new_user: UserDepartamento, db: Session) -> models.UserDepartamento:
    base_user = insert_base_user(new_user, db)

    # TODO: Adicionar o campo id_departamento
    user = models.UserDepartamento(
        id_usuario=base_user.id_usuario,
        #id_departamento=new_user.departamento_id
    )

    db.add(user)
    db.flush()

    return user

# TODO: Aguardar essas duas entidades serem criadas no banco para terminar a funcao
def insert_usuario_pro_reitor(new_user: UserProReitor, db: Session):
    pass

def insert_usuario_reitor(new_user: UserReitor, db: Session):
    pass

create_user_functions = {
    CategoriaEnum.ALUNO: insert_usuario_aluno,
    CategoriaEnum.PROFESSOR: insert_usuario_professor,
    CategoriaEnum.COORDENACAO: insert_usuario_coordenador,
    CategoriaEnum.DEPARTAMENTO: insert_usuario_departamento,
    CategoriaEnum.PRO_REITORIA: insert_usuario_pro_reitor,
    CategoriaEnum.REITORIA: insert_usuario_reitor
}

def email_already_exists(email: str, db: Session) -> bool:
    return db.query(User).filter(User.email == email).first()

@router.post("")
async def create_new_user(
        form: UserCreateForm = Depends(UserCreateForm.as_form),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
    data = {k: v for k, v in vars(form).items() if v is not None}

    new_user = TypeAdapter(UserCreate).validate_python(data)

    if email_already_exists(new_user.email, db):
        raise HTTPException(status_code=409, detail="A user with this email address already exists.")

    # Create a user in the database
    created_user = create_user_functions[new_user.categoria](new_user, db)

    # Save file to server
    await validate_file(file)
    filename = await save_file(file)

    # Create a document in the database

    return created_user