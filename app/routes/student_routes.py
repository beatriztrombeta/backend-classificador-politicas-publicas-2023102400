from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope, RoleId
from app.services.permission_service import PermissionService
from app.services.xai_service import fetch_xai_from_db, generate_groq_summary
from app.services.persona_service import get_personas_cached

router = APIRouter(prefix="/students", tags=["Alunos"])
perm = PermissionService()


@router.get("/me")
def get_my_student_data(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT, Action.READ)),
):
    if scope.role_id.name != "ALUNO":
        return {"detail": "Endpoint exclusivo para ALUNO"}

    aluno_id = next(iter(scope.aluno_ids)) if scope.aluno_ids else None
    if not aluno_id:
        return {"detail": "Aluno não vinculado"}

    row = db.execute(
        text("""
            SELECT a.id_aluno_graduacao, a.id_curso, om.classificacao
            FROM aluno a
            LEFT JOIN output_modelo om ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE a.id_aluno_graduacao = :aid
        """),
        {"aid": aluno_id},
    ).mappings().first()

    return {"data": dict(row) if row else None}


@router.get("/{aluno_id}")
def get_student_detail(
    aluno_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT, Action.READ)),
):
    perm.assert_student_access(db=db, scope=scope, aluno_id=aluno_id)

    row = db.execute(
        text("""
            WITH impactos AS (
                SELECT
                    pf.id_aluno_graduacao,
                    jsonb_object_agg(
                        UPPER(TRIM(pf.feature)),
                        pf.peso
                    ) AS impact
                FROM peso_features pf
                WHERE pf.id_aluno_graduacao = :aid
                GROUP BY pf.id_aluno_graduacao
            )
            SELECT
                a.*,
                c.nome_curso,
                u.nome_unidade,
                ca.nome_campus,
                p.periodo AS nome_periodo,
                ROUND((COALESCE(om.classificacao, 0) * 100)::numeric, 2) AS evasao,
                COALESCE(i.impact, '{}'::jsonb) AS impact
            FROM aluno a
            JOIN curso c ON c.id_curso = a.id_curso
            JOIN unidade u ON u.id_unidade = c.id_unidade
            JOIN campus ca ON ca.id_campus = u.id_campus
            LEFT JOIN periodo p ON p.id_periodo = c.id_periodo
            LEFT JOIN output_modelo om ON om.id_aluno_graduacao = a.id_aluno_graduacao
            LEFT JOIN impactos i ON i.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE a.id_aluno_graduacao = :aid
        """),
        {"aid": aluno_id},
    ).mappings().first()

    return {"data": dict(row) if row else None}


@router.get("")
def list_students(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT_LIST, Action.LIST)),
):
    if scope.role_id.name == "ALUNO":
        raise HTTPException(status_code=403, detail="Aluno não pode listar outros alunos")

    params = {
        "limit": limit,
        "offset": offset,
    }
    where = []

    if scope.role_id.name == "ADMIN":
        pass
    elif scope.role_id.name == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": [], "limit": limit, "offset": offset}
        where.append("""
            EXISTS (
                SELECT 1
                FROM aluno_disciplina adf
                WHERE adf.id_aluno_graduacao = a.id_aluno_graduacao
                  AND adf.id_disciplina = ANY(:dids)
            )
        """)
        params["dids"] = list(scope.disciplina_ids)
    elif scope.curso_ids:
        where.append("a.id_curso = ANY(:curso_ids)")
        params["curso_ids"] = list(scope.curso_ids)
    elif scope.unidade_ids:
        where.append("c.id_unidade = ANY(:unidade_ids)")
        params["unidade_ids"] = list(scope.unidade_ids)
    elif scope.campus_ids:
        where.append("u.id_campus = ANY(:campus_ids)")
        params["campus_ids"] = list(scope.campus_ids)
    else:
        return {"items": [], "limit": limit, "offset": offset}

    sql = f"""
        WITH impactos AS (
            SELECT
                pf.id_aluno_graduacao,
                jsonb_object_agg(UPPER(TRIM(pf.feature)), pf.peso) AS impact
            FROM peso_features pf
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
            a.distancia_campus AS "DISTANCIA_CAMPUS",
            c.id_periodo AS "ID_PERIODO",
            ROUND((COALESCE(om.classificacao, 0) * 100)::numeric, 2) AS "EVASAO",
            COALESCE(i.impact, '{{}}'::jsonb) AS impact
        FROM aluno a
        JOIN curso c
          ON c.id_curso = a.id_curso
        JOIN unidade u
          ON u.id_unidade = c.id_unidade
        LEFT JOIN output_modelo om
          ON om.id_aluno_graduacao = a.id_aluno_graduacao
        LEFT JOIN impactos i
          ON i.id_aluno_graduacao = a.id_aluno_graduacao
        {"WHERE " + " AND ".join(where) if where else ""}
        ORDER BY a.id_aluno_graduacao
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
    return {
    "items": [dict(r) for r in rows],
    "limit": limit,
    "offset": offset,
    "total": total,
    }

@router.get("/{aluno_id}/xai-summary")
def get_student_xai_summary(
    aluno_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT, Action.READ)),
):
    perm.assert_student_access(db=db, scope=scope, aluno_id=aluno_id)

    payload = fetch_xai_from_db(db=db, aluno_id=aluno_id)

    summary = None
    err = None
    try:
        summary, err = generate_groq_summary(payload)
    except Exception as e:
        summary = None
        err = {"type": "exception", "message": str(e)}

    payload["groq_summary"] = summary
    payload["groq_error"] = err
    return {"data": payload}


@router.get("/personas/high-risk")
def get_high_risk_personas(
    threshold: float = 0.70,
    top_n: int = 500,
    personas_n: int = 3,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT, Action.READ)),
):
    if scope.role_id == RoleId.ALUNO:
        raise HTTPException(status_code=403, detail="Not allowed for this role")

    data, error, _stale = get_personas_cached(
        db=db,
        threshold=threshold,
        top_n=top_n,
        personas_n=personas_n,
    )

    if data is None:
        raise HTTPException(
            status_code=502,
            detail=(error or {}).get("message", "Erro ao calcular personas de alto risco."),
        )

    return {"data": data}

@router.get("/{aluno_id}/subjects")
def get_student_subjects(
    aluno_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT, Action.READ)),
):
    perm.assert_student_access(db=db, scope=scope, aluno_id=aluno_id)

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
            JOIN disciplina d
              ON d.id_disciplina = ad.id_disciplina
            WHERE ad.id_aluno_graduacao = :aid
            ORDER BY d.nome_disciplina
        """),
        {"aid": aluno_id},
    ).mappings().all()

    return {"items": [dict(r) for r in rows]}