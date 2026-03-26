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