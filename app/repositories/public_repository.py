from sqlalchemy.orm import Session
from sqlalchemy import text


class PublicCatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_campus(self, q: str | None, limit: int):
        params = {"limit": limit}
        where = []
        if q:
            where.append("ca.nome_campus ILIKE :q")
            params["q"] = f"%{q}%"

        sql = f"""
            SELECT ca.id_campus, ca.nome_campus
            FROM campus ca
            {"WHERE " + " AND ".join(where) if where else ""}
            ORDER BY ca.id_campus
            LIMIT :limit
        """
        return self.db.execute(text(sql), params).mappings().all()

    def list_unidades(self, campus_id: int | None, limit: int):
        params = {"limit": limit}
        where = []
        if campus_id is not None:
            where.append("un.id_campus = :campus_id")
            params["campus_id"] = campus_id

        sql = f"""
            SELECT un.id_unidade, un.nome_unidade, un.id_campus, ca.nome_campus
            FROM unidade un
            JOIN campus ca ON ca.id_campus = un.id_campus
            {"WHERE " + " AND ".join(where) if where else ""}
            ORDER BY un.id_unidade
            LIMIT :limit
        """
        return self.db.execute(text(sql), params).mappings().all()

    def cursos_for_unidades(self, unidade_ids: list[int]):
        if not unidade_ids:
            return []

        sql = text("""
            SELECT id_curso, id_unidade, nome_curso, modalidade, id_periodo
            FROM curso
            WHERE id_unidade = ANY(:uids)
            ORDER BY id_unidade, id_curso
        """)
        return self.db.execute(sql, {"uids": unidade_ids}).mappings().all()

    def cursos_by_unidade(self, unidade_id: int, limit: int):
        sql = text("""
            SELECT id_curso, id_unidade, nome_curso, modalidade, id_periodo
            FROM curso
            WHERE id_unidade = :uid
            ORDER BY id_curso
            LIMIT :limit
        """)
        return self.db.execute(sql, {"uid": unidade_id, "limit": limit}).mappings().all()

    def list_departamentos(self, campus_id: int | None, unidade_id: int | None, q: str | None, limit: int):
        where = []
        params = {"limit": limit}

        if unidade_id is not None:
            where.append("d.id_unidade = :unidade_id")
            params["unidade_id"] = unidade_id

        if campus_id is not None:
            where.append("u.id_campus = :campus_id")
            params["campus_id"] = campus_id

        if q:
            where.append("d.nome_departamento ILIKE :q")
            params["q"] = f"%{q}%"

        sql = f"""
            SELECT d.id_departamento, d.id_unidade, d.nome_departamento,
                   u.id_campus, u.nome_unidade, ca.nome_campus
            FROM departamento d
            JOIN unidade u ON u.id_unidade = d.id_unidade
            JOIN campus ca ON ca.id_campus = u.id_campus
            {"WHERE " + " AND ".join(where) if where else ""}
            ORDER BY d.id_departamento
            LIMIT :limit
        """
        return self.db.execute(text(sql), params).mappings().all()

    def list_cursos(self, campus_id: int | None, unidade_id: int | None, q: str | None, limit: int, offset: int):
        where = []
        params = {"limit": limit, "offset": offset}

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
        return self.db.execute(text(sql), params).mappings().all()

    def disciplinas_by_curso(self, curso_id: int, limit: int):
        sql = text("""
            SELECT id_disciplina, id_curso, nome_disciplina
            FROM disciplina
            WHERE id_curso = :cid
            ORDER BY id_disciplina
            LIMIT :limit
        """)
        return self.db.execute(sql, {"cid": curso_id, "limit": limit}).mappings().all()

    def list_disciplinas(self, curso_id: int | None, unidade_id: int | None, campus_id: int | None, q: str | None, limit: int):
        where = []
        params = {"limit": limit}

        joins = "FROM disciplina d"
        if unidade_id is not None or campus_id is not None:
            joins += " JOIN curso c ON c.id_curso = d.id_curso JOIN unidade u ON u.id_unidade = c.id_unidade"

        if curso_id is not None:
            where.append("d.id_curso = :curso_id")
            params["curso_id"] = curso_id

        if unidade_id is not None:
            where.append("c.id_unidade = :unidade_id")
            params["unidade_id"] = unidade_id

        if campus_id is not None:
            where.append("u.id_campus = :campus_id")
            params["campus_id"] = campus_id

        if q:
            where.append("d.nome_disciplina ILIKE :q")
            params["q"] = f"%{q}%"

        sql = f"""
            SELECT d.id_disciplina, d.id_curso, d.nome_disciplina
            {joins}
            {"WHERE " + " AND ".join(where) if where else ""}
            ORDER BY d.id_disciplina
            LIMIT :limit
        """
        return self.db.execute(text(sql), params).mappings().all()

    def list_proreitorias(self, q: str | None, limit: int):
        params = {"limit": limit}
        where = []
        if q:
            where.append("tp.nome_proreitoria ILIKE :q")
            params["q"] = f"%{q}%"

        sql = f"""
            SELECT tp.id_tipo_proreitoria AS id_proreitoria, tp.nome_proreitoria
            FROM tipo_proreitoria tp
            {"WHERE " + " AND ".join(where) if where else ""}
            ORDER BY tp.id_tipo_proreitoria
            LIMIT :limit
        """
        return self.db.execute(text(sql), params).mappings().all()