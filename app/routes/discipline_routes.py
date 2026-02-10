from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])


@router.get("")
def list_disciplinas(
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    if scope.role_id.name == "ADMIN":
        rows = db.execute(
            text("""
                SELECT d.id_disciplina, d.id_curso, d.nome_disciplina
                FROM disciplina d
                ORDER BY d.id_disciplina
                LIMIT :limit
            """),
            {"limit": limit},
        ).mappings().all()
        return {"items": [dict(r) for r in rows]}

    if scope.role_id.name == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": []}
        rows = db.execute(
            text("""
                SELECT d.id_disciplina, d.id_curso, d.nome_disciplina
                FROM disciplina d
                WHERE d.id_disciplina = ANY(:dids)
                ORDER BY d.id_disciplina
                LIMIT :limit
            """),
            {"dids": list(scope.disciplina_ids), "limit": limit},
        ).mappings().all()
        return {"items": [dict(r) for r in rows]}

    where = []
    params = {"limit": limit}

    if scope.curso_ids:
        where.append("d.id_curso = ANY(:cids)")
        params["cids"] = list(scope.curso_ids)
    elif scope.unidade_ids:
        where.append("c.id_unidade = ANY(:uids)")
        params["uids"] = list(scope.unidade_ids)
    elif scope.campus_ids:
        where.append("u.id_campus = ANY(:campus_ids)")
        params["campus_ids"] = list(scope.campus_ids)
    else:
        return {"items": []}

    sql = f"""
        SELECT d.id_disciplina, d.id_curso, d.nome_disciplina
        FROM disciplina d
        JOIN curso c ON c.id_curso = d.id_curso
        JOIN unidade u ON u.id_unidade = c.id_unidade
        WHERE {" AND ".join(where)}
        ORDER BY d.id_disciplina
        LIMIT :limit
    """
    rows = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(r) for r in rows]}