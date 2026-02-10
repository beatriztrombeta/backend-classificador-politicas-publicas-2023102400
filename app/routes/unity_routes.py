from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope

router = APIRouter(prefix="/unidades", tags=["Unidades"])


def _unidade_scope_where(scope: AccessScope):
    where = []
    params = {}

    if scope.role_id.name == "ADMIN":
        return where, params

    if scope.unidade_ids:
        where.append("un.id_unidade = ANY(:unidade_ids)")
        params["unidade_ids"] = list(scope.unidade_ids)
        return where, params

    if scope.campus_ids:
        where.append("un.id_campus = ANY(:campus_ids)")
        params["campus_ids"] = list(scope.campus_ids)
        return where, params

    where.append("1=0")
    return where, params


@router.get("")
def list_unidades(
    include_courses: bool = Query(True),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    where, params = _unidade_scope_where(scope)
    params["limit"] = limit

    sql = f"""
        SELECT un.id_unidade, un.nome_unidade, un.id_campus, ca.nome_campus
        FROM unidade un
        JOIN campus ca ON ca.id_campus = un.id_campus
        {"WHERE " + " AND ".join(where) if where else ""}
        ORDER BY un.id_unidade
        LIMIT :limit
    """
    unidades = [dict(r) for r in db.execute(text(sql), params).mappings().all()]

    if not include_courses:
        return {"items": unidades}

    unidade_ids = [int(u["id_unidade"]) for u in unidades]
    if not unidade_ids:
        return {"items": []}

    cursos = db.execute(
        text("""
            SELECT id_curso, id_unidade, nome_curso, modalidade, id_periodo
            FROM curso
            WHERE id_unidade = ANY(:uids)
            ORDER BY id_unidade, id_curso
        """),
        {"uids": unidade_ids},
    ).mappings().all()

    by_unidade = {}
    for c in cursos:
        by_unidade.setdefault(int(c["id_unidade"]), []).append(dict(c))

    for u in unidades:
        u["courses"] = by_unidade.get(int(u["id_unidade"]), [])

    return {"items": unidades}


@router.get("/{unidade_id}/cursos")
def courses_by_unidade(
    unidade_id: int,
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    # Garante que a unidade está no escopo (mesma lógica de listagem)
    where, params = _unidade_scope_where(scope)
    where.append("un.id_unidade = :uid")
    params["uid"] = unidade_id

    allowed = db.execute(
        text(f"""
            SELECT 1
            FROM unidade un
            WHERE {" AND ".join(where)}
            LIMIT 1
        """),
        params,
    ).first()

    if not allowed:
        return {"items": []}

    rows = db.execute(
        text("""
            SELECT id_curso, id_unidade, nome_curso, modalidade, id_periodo
            FROM curso
            WHERE id_unidade = :uid
            ORDER BY id_curso
            LIMIT :limit
        """),
        {"uid": unidade_id, "limit": limit},
    ).mappings().all()

    return {"items": [dict(r) for r in rows]}