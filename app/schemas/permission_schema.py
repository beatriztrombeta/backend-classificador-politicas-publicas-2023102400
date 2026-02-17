from enum import IntEnum, Enum
from pydantic import BaseModel, Field
from typing import Set

class RoleId(IntEnum):
    ADMIN = 1
    REITORIA = 2
    PRO_REITORIA = 3
    DEPARTAMENTO = 4
    COORDENACAO = 5
    PROFESSOR = 6
    ALUNO = 7

class Resource(str, Enum):
    STUDENT = "student"
    STUDENT_LIST = "student_list"
    REPORTS = "reports"     
    USER_MGMT = "user_mgmt"

class Action(str, Enum):
    READ = "read"
    LIST = "list"
    MANAGE = "manage"

class AccessScope(BaseModel):
    role_id: RoleId = Field(...)
    user_id: int = Field(...)

    campus_ids: Set[int] = Field(default_factory=set)
    unidade_ids: Set[int] = Field(default_factory=set)
    departamento_ids: Set[int] = Field(default_factory=set)
    curso_ids: Set[int] = Field(default_factory=set)
    disciplina_ids: Set[int] = Field(default_factory=set)
    aluno_ids: Set[int] = Field(default_factory=set)

    proreitoria_ids: Set[int] = Field(default_factory=set)