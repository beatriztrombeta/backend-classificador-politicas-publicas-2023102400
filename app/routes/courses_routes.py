from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope
from app.utils.evasion_risk import calculate_course_evasion_risk
from app.schemas.evasion_risk_schema import CourseEvasionRiskResponse

router = APIRouter(prefix="/cursos", tags=["Cursos"])

def _can_access_course(db: Session, scope: AccessScope, curso_id: int) -> bool:
    role = scope.role_id.name

    if role == "ADMIN":
        return True

    if role == "ALUNO":
        return False

    if role == "COORD":
        return bool(scope.curso_ids and curso_id in scope.curso_ids)

    if role == "PROFESSOR":
        if not scope.disciplina_ids:
            return False

        chk = db.execute(
            text("""
                SELECT 1
                FROM disciplina d
                WHERE d.id_curso = :cid
                  AND d.id_disciplina = ANY(:dids)
                LIMIT 1
            """),
            {"cid": curso_id, "dids": list(scope.disciplina_ids)},
        ).first()

        return bool(chk)

    params = {"cid": curso_id}
    where = ["c.id_curso = :cid"]

    if scope.unidade_ids:
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
            FROM curso c
            JOIN unidade u ON u.id_unidade = c.id_unidade
            WHERE {" AND ".join(where)}
            LIMIT 1
        """),
        params,
    ).first()

    return bool(chk)

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

@router.get("/{curso_id}/alunos")
def students_by_curso(
    curso_id: int,
    limit: int = Query(300, ge=1, le=2000),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT_LIST, Action.LIST)),
):
    if not _can_access_course(db, scope, curso_id):
        return {"items": []}

    rows = db.execute(
        text("""
            WITH impactos AS (
                SELECT
                    pf.id_aluno_graduacao,
                    jsonb_object_agg(UPPER(TRIM(pf.descricao)), pf.peso) AS impact
                FROM peso_features pf
                WHERE pf.id_aluno_graduacao IN (
                    SELECT a.id_aluno_graduacao
                    FROM aluno a
                    WHERE a.id_curso = :cid
                )
                GROUP BY pf.id_aluno_graduacao
            )
            SELECT
                a.id_aluno_graduacao AS "ID_ALUNO_GRADUACAO",
                a.cidade_origem AS "CIDADE_ORIGEM",
                a.raca_cor AS "RACA_COR",
                a.sexo AS "SEXO",
                a.ensino_medio AS "ENSINO_MEDIO",
                a.cotas AS "COTAS",
                a.tipo_ingresso AS "TIPO_INGRESSO",
                a.situacao AS "SITUACAO",
                a.ano_matricula AS "ANO_MATRICULA",
                a.avg_nota AS "AVG_NOTA",
                a.max_nota AS "MAX_NOTA",
                a.min_nota AS "MIN_NOTA",
                a.median_nota AS "MEDIAN_NOTA",
                a.avg_frequencia AS "AVG_FREQUENCIA",
                a.max_frequencia AS "MAX_FREQUENCIA",
                a.min_frequencia AS "MIN_FREQUENCIA",
                a.median_frequencia AS "MEDIAN_FREQUENCIA",
                a.perc_reprovacao AS "PERC_REPROVACAO",
                a.perc_exames AS "PERC_EXAMES",
                a.unique_disciplinas AS "QTD_DISCIPLINAS",
                a.ano_nascimento AS "ANO_NASCIMENTO",
                NULL::INTEGER AS "MES_NASCIMENTO",
                a.idade_matricula AS "IDADE_MATRICULA",
                NULL::NUMERIC AS "DISTANCIA_CAMPUS",
                c.id_periodo AS "ID_PERIODO",
                ROUND((COALESCE(om.classificacao, 0) * 100)::numeric, 2) AS "EVASAO",
                COALESCE(i.impact, '{}'::jsonb) AS impact
            FROM aluno a
            JOIN curso c
              ON c.id_curso = a.id_curso
            LEFT JOIN output_modelo om
              ON om.id_aluno_graduacao = a.id_aluno_graduacao
            LEFT JOIN impactos i
              ON i.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE a.id_curso = :cid
            ORDER BY a.id_aluno_graduacao
            LIMIT :limit
        """),
        {"cid": curso_id, "limit": limit},
    ).mappings().all()

    return {"items": [dict(r) for r in rows]}

@router.get("/{curso_id}/risco-evasao", response_model=CourseEvasionRiskResponse)
def course_evasion_risk(
    curso_id: int,
    high_risk_threshold: float = Query(0.7, ge=0, le=1),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.REPORTS, Action.READ)),
):
    if not _can_access_course(db, scope, curso_id):
        raise HTTPException(status_code=403, detail="Acesso negado ao curso.")

    result = calculate_course_evasion_risk(
        db=db,
        curso_id=curso_id,
        high_risk_threshold=high_risk_threshold
    )

    if not result:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")

    return result