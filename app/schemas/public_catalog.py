from pydantic import BaseModel
from typing import Optional, List


class CampusOut(BaseModel):
    id_campus: int
    nome_campus: str


class UnidadeOut(BaseModel):
    id_unidade: int
    nome_unidade: str
    id_campus: int
    nome_campus: str
    courses: Optional[List[dict]] = None


class CursoOut(BaseModel):
    id_curso: int
    id_unidade: int
    nome_curso: str
    modalidade: Optional[str] = None
    id_periodo: Optional[int] = None


class DepartamentoOut(BaseModel):
    id_departamento: int
    id_unidade: int
    nome_departamento: str
    id_campus: int
    nome_unidade: str
    nome_campus: str


class DisciplinaOut(BaseModel):
    id_disciplina: int
    id_curso: int
    nome_disciplina: str


class ProreitoriaOut(BaseModel):
    id_proreitoria: int
    nome_proreitoria: str


class ItemsResponse(BaseModel):
    items: list