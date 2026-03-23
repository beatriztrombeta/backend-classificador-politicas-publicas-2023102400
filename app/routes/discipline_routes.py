from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])


def _can_access_disciplina(db: Session, scope: AccessScope, disciplina_id: int) -> bool:
    if scope.role_id.name == "ADMIN":
        return True

    if scope.role_id.name == "PROFESSOR":
        return bool(scope.disciplina_ids and disciplina_id in scope.disciplina_ids)

    params = {"did": disciplina_id}
    where = ["d.id_disciplina = :did"]

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
        return False

    chk = db.execute(
        text(f"""
            SELECT 1
            FROM disciplina d
            JOIN curso c ON c.id_curso = d.id_curso
            JOIN unidade u ON u.id_unidade = c.id_unidade
            WHERE {" AND ".join(where)}
            LIMIT 1
        """),
        params,
    ).first()

    return bool(chk)

@router.get("")
def list_disciplinas(
    limit: int = Query(5000, ge=1, le=20000),
    offset: int = Query(0, ge=0, le=200000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    params = {"limit": limit, "offset": offset}
    where = []

    if scope.role_id.name == "ADMIN":
        pass
    elif scope.role_id.name == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": [], "limit": limit, "offset": offset}
        where.append("d.id_disciplina = ANY(:dids)")
        params["dids"] = list(scope.disciplina_ids)
    elif scope.curso_ids:
        where.append("d.id_curso = ANY(:cids)")
        params["cids"] = list(scope.curso_ids)
    elif scope.unidade_ids:
        where.append("c.id_unidade = ANY(:uids)")
        params["uids"] = list(scope.unidade_ids)
    elif scope.campus_ids:
        where.append("u.id_campus = ANY(:campus_ids)")
        params["campus_ids"] = list(scope.campus_ids)
    else:
        return {"items": [], "limit": limit, "offset": offset}

    sql = f"""
        SELECT
            MIN(d.id_disciplina) AS id_disciplina,
            ARRAY_AGG(d.id_disciplina ORDER BY d.id_disciplina) AS disciplina_ids,
            d.nome_disciplina,
            COUNT(DISTINCT ad.id_aluno_graduacao) AS total_alunos
        FROM disciplina d
        JOIN curso c ON c.id_curso = d.id_curso
        JOIN unidade u ON u.id_unidade = c.id_unidade
        LEFT JOIN aluno_disciplina ad ON ad.id_disciplina = d.id_disciplina
        {"WHERE " + " AND ".join(where) if where else ""}
        GROUP BY d.nome_disciplina
        ORDER BY d.nome_disciplina
        LIMIT :limit OFFSET :offset
    """

    count_sql = f"""
        SELECT COUNT(*)
        FROM (
            SELECT d.nome_disciplina
            FROM disciplina d
            JOIN curso c ON c.id_curso = d.id_curso
            JOIN unidade u ON u.id_unidade = c.id_unidade
            {"WHERE " + " AND ".join(where) if where else ""}
            GROUP BY d.nome_disciplina
        ) sub
    """

    total = db.execute(text(count_sql), params).scalar()
    rows = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(r) for r in rows], "limit": limit, "offset": offset, "total": total}


@router.get("/{disciplina_id}/alunos")
def students_by_disciplina(
    disciplina_id: int,
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT_LIST, Action.LIST)),
):
    if not _can_access_disciplina(db, scope, disciplina_id):
        return {"items": []}

    rows = db.execute(
        text("""
            SELECT
                ad.id_aluno_graduacao,
                a.id_curso,
                d.nome_disciplina,
                ad.conceito,
                ad.frequencia,
                ad.tipo_efetivacao,
                ad.tipo_nota,
                ad.nota
            FROM aluno_disciplina ad
            JOIN disciplina d
              ON d.id_disciplina = ad.id_disciplina
            JOIN aluno a
              ON a.id_aluno_graduacao = ad.id_aluno_graduacao
            WHERE ad.id_disciplina = :did
            ORDER BY ad.id_aluno_graduacao
            LIMIT :limit
        """),
        {"did": disciplina_id, "limit": limit},
    ).mappings().all()

    return {"items": [dict(r) for r in rows]}

@router.get("/alunos")
def students_by_disciplina_group(
    ids: str = Query(..., description="IDs de disciplina separados por vírgula"),
    limit: int = Query(5000, ge=1, le=20000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT_LIST, Action.LIST)),
):
    disciplina_ids = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    if not disciplina_ids:
        return {"items": []}

    if scope.role_id.name == "PROFESSOR":
        allowed = set(scope.disciplina_ids or [])
        disciplina_ids = [d for d in disciplina_ids if d in allowed]
        if not disciplina_ids:
            return {"items": []}

    rows = db.execute(
        text("""
            SELECT
                ad.id_aluno_graduacao,
                ad.id_disciplina,
                d.nome_disciplina,
                ad.conceito,
                ad.frequencia,
                ad.tipo_efetivacao,
                ad.tipo_nota,
                ad.nota
            FROM aluno_disciplina ad
            JOIN disciplina d ON d.id_disciplina = ad.id_disciplina
            WHERE ad.id_disciplina = ANY(:dids)
            ORDER BY ad.id_aluno_graduacao, ad.id_disciplina
            LIMIT :limit
        """),
        {"dids": disciplina_ids, "limit": limit},
    ).mappings().all()

    return {"items": [dict(r) for r in rows]}