from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope

router = APIRouter(prefix="/cursos", tags=["Cursos"])

@router.get("/{curso_id}/disciplinas")
def disciplinas_by_curso(
    curso_id: int,
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    if scope.role_id.name == "ALUNO":
        return {"items": []}

    if scope.role_id.name == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": []}
        rows = db.execute(
            text("""
                SELECT d.id_disciplina, d.id_curso, d.nome_disciplina
                FROM disciplina d
                WHERE d.id_curso = :cid AND d.id_disciplina = ANY(:dids)
                ORDER BY d.id_disciplina
                LIMIT :limit
            """),
            {"cid": curso_id, "dids": list(scope.disciplina_ids), "limit": limit},
        ).mappings().all()
        return {"items": [dict(r) for r in rows]}

    allowed = False
    if scope.role_id.name == "ADMIN":
        allowed = True
    elif scope.curso_ids and curso_id in scope.curso_ids:
        allowed = True
    else:
        params = {"cid": curso_id}
        where = ["c.id_curso = :cid"]
        if scope.unidade_ids:
            where.append("c.id_unidade = ANY(:uids)")
            params["uids"] = list(scope.unidade_ids)
        elif scope.campus_ids:
            where.append("u.id_campus = ANY(:campus_ids)")
            params["campus_ids"] = list(scope.campus_ids)
        else:
            allowed = False

        if len(where) > 1:
            chk = db.execute(
                text(f"""
                    SELECT 1
                    FROM curso c
                    JOIN unidade u ON u.id_unidade = c.id_unidade
                    WHERE {" AND ".join(where)}
                    LIMIT 1
                """),
                params,
            ).first()
            allowed = bool(chk)

    if not allowed:
        return {"items": []}

    rows = db.execute(
        text("""
            SELECT id_disciplina, id_curso, nome_disciplina
            FROM disciplina
            WHERE id_curso = :cid
            ORDER BY id_disciplina
            LIMIT :limit
        """),
        {"cid": curso_id, "limit": limit},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}

@router.get("")
def list_cursos(
    campus_id: int | None = Query(None),
    unidade_id: int | None = Query(None),
    q: str | None = Query(None, description="Busca por nome do curso"),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0, le=200000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    where = []
    params = {"limit": limit, "offset": offset}

    role = scope.role_id.name

    if role == "ADMIN":
        pass

    elif role == "COORD":
        if not scope.curso_ids:
            return {"items": [], "limit": limit, "offset": offset}
        where.append("c.id_curso = ANY(:curso_ids)")
        params["curso_ids"] = list(scope.curso_ids)

    elif role == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": [], "limit": limit, "offset": offset}
        where.append("""
            c.id_curso IN (
                SELECT d.id_curso
                FROM disciplina d
                WHERE d.id_disciplina = ANY(:disciplina_ids)
            )
        """)
        params["disciplina_ids"] = list(scope.disciplina_ids)

    elif role == "ALUNO":
        if not scope.aluno_ids:
            return {"items": [], "limit": limit, "offset": offset}
        where.append("""
            c.id_curso IN (
                SELECT a.id_curso
                FROM aluno a
                WHERE a.id_aluno_graduacao = ANY(:aluno_ids)
            )
        """)
        params["aluno_ids"] = list(scope.aluno_ids)

    else:
        if scope.unidade_ids:
            where.append("c.id_unidade = ANY(:unidade_ids)")
            params["unidade_ids"] = list(scope.unidade_ids)
        elif scope.campus_ids:
            where.append("u.id_campus = ANY(:campus_ids)")
            params["campus_ids"] = list(scope.campus_ids)
        else:
            return {"items": [], "limit": limit, "offset": offset}

    if unidade_id is not None:
        where.append("c.id_unidade = :unidade_id")
        params["unidade_id"] = unidade_id

    if campus_id is not None:
        where.append("u.id_campus = :campus_id")
        params["campus_id"] = campus_id

    if q:
        where.append("c.nome_curso ILIKE :q")
        params["q"] = f"%{q}%"

    sql = f"""
        SELECT
            c.id_curso,
            c.id_unidade,
            c.id_periodo,
            c.nome_curso,
            c.modalidade,
            p.periodo AS nome_periodo,
            u.id_campus,
            u.nome_unidade,
            ca.nome_campus
        FROM curso c
        JOIN unidade u ON u.id_unidade = c.id_unidade
        JOIN campus ca ON ca.id_campus = u.id_campus
        JOIN periodo p ON p.id_periodo = c.id_periodo
        {"WHERE " + " AND ".join([f"({w})" for w in where]) if where else ""}
        ORDER BY c.id_curso
        LIMIT :limit OFFSET :offset
    """

    rows = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(r) for r in rows], "limit": limit, "offset": offset}
