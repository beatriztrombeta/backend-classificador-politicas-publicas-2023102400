from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def calculate_course_evasion_risk(db: Session, curso_id: int, high_risk_threshold: float = 0.7) -> dict:
    row = db.execute(
        text("""
            SELECT
                c.id_curso,
                c.nome_curso,
                c.id_unidade,
                COUNT(a.id_aluno_graduacao) AS total_alunos,
                COALESCE(AVG(om.classificacao), 0) AS risco_medio,
                COALESCE(
                    AVG(
                        CASE
                            WHEN om.classificacao >= :threshold THEN 1.0
                            ELSE 0.0
                        END
                    ),
                    0
                ) AS proporcao_alto_risco
            FROM curso c
            LEFT JOIN aluno a
                ON a.id_curso = c.id_curso
            LEFT JOIN output_modelo om
                ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE c.id_curso = :curso_id
            GROUP BY c.id_curso, c.nome_curso, c.id_unidade
        """),
        {"curso_id": curso_id, "threshold": high_risk_threshold},
    ).mappings().first()

    if not row:
        return {}

    return {
        "id_curso": row["id_curso"],
        "nome_curso": row["nome_curso"],
        "id_unidade": row["id_unidade"],
        "total_alunos": int(row["total_alunos"] or 0),
        "risco_medio": float(row["risco_medio"] or 0),
        "risco_percentual": round(float(row["risco_medio"] or 0) * 100, 2),
        "proporcao_alto_risco": float(row["proporcao_alto_risco"] or 0),
        "proporcao_alto_risco_percentual": round(float(row["proporcao_alto_risco"] or 0) * 100, 2),
        "limiar_alto_risco": high_risk_threshold,
    }


def calculate_courses_evasion_risk_batch(
    db: Session,
    curso_ids: list[int],
    high_risk_threshold: float = 0.7,
    extra_where: Optional[list[str]] = None,
    extra_params: Optional[dict] = None,
) -> dict[int, dict]:
    """
    Mesma agregação de calculate_course_evasion_risk, mas pra N cursos em 1 query só
    (GROUP BY id_curso, filtrando por ANY(:curso_ids) em vez de um id por vez).
    `extra_where`/`extra_params` permitem plugar um filtro de escopo na mesma query.
    Retorna um dict {id_curso: resultado}.
    """
    if not curso_ids:
        return {}

    where = ["c.id_curso = ANY(:curso_ids)"]
    params = {"curso_ids": curso_ids, "threshold": high_risk_threshold}

    if extra_where:
        where.extend(extra_where)
    if extra_params:
        params.update(extra_params)

    rows = db.execute(
        text(f"""
            SELECT
                c.id_curso,
                c.nome_curso,
                c.id_unidade,
                COUNT(a.id_aluno_graduacao) AS total_alunos,
                COALESCE(AVG(om.classificacao), 0) AS risco_medio,
                COALESCE(
                    AVG(
                        CASE
                            WHEN om.classificacao >= :threshold THEN 1.0
                            ELSE 0.0
                        END
                    ),
                    0
                ) AS proporcao_alto_risco
            FROM curso c
            JOIN unidade u
                ON u.id_unidade = c.id_unidade
            LEFT JOIN aluno a
                ON a.id_curso = c.id_curso
            LEFT JOIN output_modelo om
                ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE {" AND ".join(where)}
            GROUP BY c.id_curso, c.nome_curso, c.id_unidade
        """),
        params,
    ).mappings().all()

    result: dict[int, dict] = {}
    for row in rows:
        result[int(row["id_curso"])] = {
            "id_curso": row["id_curso"],
            "nome_curso": row["nome_curso"],
            "id_unidade": row["id_unidade"],
            "total_alunos": int(row["total_alunos"] or 0),
            "risco_medio": float(row["risco_medio"] or 0),
            "risco_percentual": round(float(row["risco_medio"] or 0) * 100, 2),
            "proporcao_alto_risco": float(row["proporcao_alto_risco"] or 0),
            "proporcao_alto_risco_percentual": round(float(row["proporcao_alto_risco"] or 0) * 100, 2),
            "limiar_alto_risco": high_risk_threshold,
        }
    return result


def calculate_unidade_evasion_risk(db: Session, unidade_id: int, high_risk_threshold: float = 0.7) -> dict:
    row = db.execute(
        text("""
            SELECT
                u.id_unidade,
                u.nome_unidade,
                COUNT(a.id_aluno_graduacao) AS total_alunos,
                COALESCE(AVG(om.classificacao), 0) AS risco_medio,
                COALESCE(
                    AVG(
                        CASE
                            WHEN om.classificacao >= :threshold THEN 1.0
                            ELSE 0.0
                        END
                    ),
                    0
                ) AS proporcao_alto_risco
            FROM unidade u
            LEFT JOIN curso c
                ON c.id_unidade = u.id_unidade
            LEFT JOIN aluno a
                ON a.id_curso = c.id_curso
            LEFT JOIN output_modelo om
                ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE u.id_unidade = :unidade_id
            GROUP BY u.id_unidade, u.nome_unidade
        """),
        {"unidade_id": unidade_id, "threshold": high_risk_threshold},
    ).mappings().first()

    if not row:
        return {}

    return {
        "id_unidade": row["id_unidade"],
        "nome_unidade": row["nome_unidade"],
        "total_alunos": int(row["total_alunos"] or 0),
        "risco_medio": float(row["risco_medio"] or 0),
        "risco_percentual": round(float(row["risco_medio"] or 0) * 100, 2),
        "proporcao_alto_risco": float(row["proporcao_alto_risco"] or 0),
        "proporcao_alto_risco_percentual": round(float(row["proporcao_alto_risco"] or 0) * 100, 2),
        "limiar_alto_risco": high_risk_threshold,
    }


def calculate_unidades_evasion_risk_batch(
    db: Session,
    unidade_ids: list[int],
    high_risk_threshold: float = 0.7,
    extra_where: Optional[list[str]] = None,
    extra_params: Optional[dict] = None,
) -> dict[int, dict]:
    """
    Mesma agregação de calculate_unidade_evasion_risk, mas pra N unidades em 1 query só.
    `extra_where`/`extra_params` permitem plugar o filtro de escopo (_unidade_scope_where)
    na mesma query, pra nunca calcular/retornar dado de unidade fora do escopo do usuário.
    """
    if not unidade_ids:
        return {}

    where = ["u.id_unidade = ANY(:unidade_ids)"]
    params = {"unidade_ids": unidade_ids, "threshold": high_risk_threshold}

    if extra_where:
        where.extend(extra_where)
    if extra_params:
        params.update(extra_params)

    rows = db.execute(
        text(f"""
            SELECT
                u.id_unidade,
                u.nome_unidade,
                COUNT(a.id_aluno_graduacao) AS total_alunos,
                COALESCE(AVG(om.classificacao), 0) AS risco_medio,
                COALESCE(
                    AVG(
                        CASE
                            WHEN om.classificacao >= :threshold THEN 1.0
                            ELSE 0.0
                        END
                    ),
                    0
                ) AS proporcao_alto_risco
            FROM unidade u
            LEFT JOIN curso c
                ON c.id_unidade = u.id_unidade
            LEFT JOIN aluno a
                ON a.id_curso = c.id_curso
            LEFT JOIN output_modelo om
                ON om.id_aluno_graduacao = a.id_aluno_graduacao
            WHERE {" AND ".join(where)}
            GROUP BY u.id_unidade, u.nome_unidade
        """),
        params,
    ).mappings().all()

    result: dict[int, dict] = {}
    for row in rows:
        result[int(row["id_unidade"])] = {
            "id_unidade": row["id_unidade"],
            "nome_unidade": row["nome_unidade"],
            "total_alunos": int(row["total_alunos"] or 0),
            "risco_medio": float(row["risco_medio"] or 0),
            "risco_percentual": round(float(row["risco_medio"] or 0) * 100, 2),
            "proporcao_alto_risco": float(row["proporcao_alto_risco"] or 0),
            "proporcao_alto_risco_percentual": round(float(row["proporcao_alto_risco"] or 0) * 100, 2),
            "limiar_alto_risco": high_risk_threshold,
        }
    return result