from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope, RoleId
from app.services.permission_service import PermissionService
from app.services.xai_service import fetch_xai_from_db, generate_groq_summary
from app.services.persona_service import fetch_high_risk_ids, aggregate_signals, population_stats
from app.services.persona_service import generate_personas_with_groq, build_persona_inputs

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
            SELECT a.*, om.classificacao
            FROM aluno a
            LEFT JOIN output_modelo om ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE a.id_aluno_graduacao = :aid
        """),
        {"aid": aluno_id},
    ).mappings().first()

    return {"data": dict(row) if row else None}


@router.get("")
def list_students(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.STUDENT_LIST, Action.LIST)),
):
    if scope.role_id.name == "ALUNO":
        return {"detail": "Aluno não pode listar outros alunos"}

    if scope.role_id.name == "ADMIN":
        rows = db.execute(text("SELECT id_aluno_graduacao, id_curso FROM aluno LIMIT 200")).mappings().all()
        return {"items": [dict(r) for r in rows]}

    if scope.role_id.name == "PROFESSOR":
        if not scope.disciplina_ids:
            return {"items": []}
        rows = db.execute(
            text("""
                SELECT DISTINCT a.id_aluno_graduacao, a.id_curso
                FROM aluno a
                JOIN aluno_disciplina ad ON ad.id_aluno_graduacao = a.id_aluno_graduacao
                WHERE ad.id_disciplina = ANY(:dids)
                LIMIT 200
            """),
            {"dids": list(scope.disciplina_ids)},
        ).mappings().all()
        return {"items": [dict(r) for r in rows]}

    where = []
    params = {}

    if scope.curso_ids:
        where.append("a.id_curso = ANY(:curso_ids)")
        params["curso_ids"] = list(scope.curso_ids)
    elif scope.unidade_ids:
        where.append("c.id_unidade = ANY(:unidade_ids)")
        params["unidade_ids"] = list(scope.unidade_ids)
    elif scope.campus_ids:
        where.append("u.id_campus = ANY(:campus_ids)")
        params["campus_ids"] = list(scope.campus_ids)
    else:
        return {"items": []}

    sql = f"""
        SELECT a.id_aluno_graduacao, a.id_curso
        FROM aluno a
        JOIN curso c ON c.id_curso = a.id_curso
        JOIN unidade u ON u.id_unidade = c.id_unidade
        WHERE {" AND ".join(where)}
        LIMIT 200
    """
    rows = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(r) for r in rows]}

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

    ids = fetch_high_risk_ids(db, threshold=threshold, top_n=top_n)
    pop = population_stats(db, threshold=threshold)

    if not ids:
        return {
            "data": {
                "population": pop,
                "signals": {"top_risk_drivers": []},
                "groups": [],
                "personas": [],
                "groq_error": None,
            }
        }

    inputs = build_persona_inputs(
        db=db,
        high_risk_ids=ids,
        threshold=threshold,
        personas_n=personas_n,
    )

    signals = aggregate_signals(db, aluno_ids=ids)

    personas, groq_error = generate_personas_with_groq(
        payload=inputs,
        personas_n=personas_n,
    )

    return {
        "data": {
            "population": inputs["population"],
            "signals": {"top_risk_drivers": signals[:10]},
            "groups": inputs["groups"],
            "personas": personas,
            "groq_error": groq_error,
        }
    }