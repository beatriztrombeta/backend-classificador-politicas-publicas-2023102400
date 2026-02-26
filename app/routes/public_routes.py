from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.controllers.public_controller import PublicCatalogController

router = APIRouter(prefix="/public", tags=["Public Catalog"])


def get_controller(db: Session = Depends(get_db)) -> PublicCatalogController:
    return PublicCatalogController(db)


@router.get("/campus")
def list_campus(
    q: str | None = Query(None, description="Busca por nome do campus"),
    limit: int = Query(200, ge=1, le=2000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_campus(q=q, limit=limit)


@router.get("/unidades")
def list_unidades(
    campus_id: int | None = Query(None),
    include_courses: bool = Query(False, description="Se true, devolve cursos aninhados em cada unidade"),
    limit: int = Query(500, ge=1, le=2000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_unidades(campus_id=campus_id, include_courses=include_courses, limit=limit)


@router.get("/unidades/{unidade_id}/cursos")
def cursos_by_unidade(
    unidade_id: int,
    limit: int = Query(500, ge=1, le=2000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.cursos_by_unidade(unidade_id=unidade_id, limit=limit)


@router.get("/departamentos")
def list_departamentos(
    campus_id: int | None = Query(None, description="Filtra departamentos por campus (via unidade)"),
    unidade_id: int | None = Query(None, description="Filtra departamentos por unidade"),
    q: str | None = Query(None, description="Busca por nome do departamento"),
    limit: int = Query(500, ge=1, le=2000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_departamentos(campus_id=campus_id, unidade_id=unidade_id, q=q, limit=limit)


@router.get("/cursos")
def list_cursos(
    campus_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    q: str | None = Query(None, description="Busca por nome do curso"),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0, le=200000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_cursos(campus_id=campus_id, unidade_id=unidade_id, q=q, limit=limit, offset=offset)


@router.get("/cursos/{curso_id}/disciplinas")
def list_disciplinas_by_curso(
    curso_id: int,
    limit: int = Query(1000, ge=1, le=5000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_disciplinas_by_curso(curso_id=curso_id, limit=limit)


@router.get("/disciplinas")
def list_disciplinas(
    curso_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    campus_id: int | None = Query(None),
    q: str | None = Query(None, description="Busca por nome da disciplina"),
    limit: int = Query(1000, ge=1, le=5000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_disciplinas(curso_id=curso_id, unidade_id=unidade_id, campus_id=campus_id, q=q, limit=limit)


@router.get("/proreitorias")
def list_proreitorias(
    q: str | None = Query(None, description="Busca por nome da pró-reitoria"),
    limit: int = Query(200, ge=1, le=2000),
    ctl: PublicCatalogController = Depends(get_controller),
):
    return ctl.list_proreitorias(q=q, limit=limit)