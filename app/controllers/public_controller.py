from sqlalchemy.orm import Session
from app.repositories.public_repository import PublicCatalogRepository


class PublicCatalogController:
    def __init__(self, db: Session):
        self.repo = PublicCatalogRepository(db)

    def list_campus(self, q: str | None, limit: int):
        rows = self.repo.list_campus(q=q, limit=limit)
        return {"items": [dict(r) for r in rows]}

    def list_unidades(self, campus_id: int | None, include_courses: bool, limit: int):
        unidades_rows = self.repo.list_unidades(campus_id=campus_id, limit=limit)
        unidades = [dict(r) for r in unidades_rows]

        if not include_courses:
            return {"items": unidades}

        unidade_ids = [int(u["id_unidade"]) for u in unidades]
        cursos_rows = self.repo.cursos_for_unidades(unidade_ids)
        by_unidade: dict[int, list[dict]] = {}
        for c in cursos_rows:
            by_unidade.setdefault(int(c["id_unidade"]), []).append(dict(c))

        for u in unidades:
            u["courses"] = by_unidade.get(int(u["id_unidade"]), [])

        return {"items": unidades}

    def cursos_by_unidade(self, unidade_id: int, limit: int):
        rows = self.repo.cursos_by_unidade(unidade_id=unidade_id, limit=limit)
        return {"items": [dict(r) for r in rows]}

    def list_departamentos(self, campus_id: int | None, unidade_id: int | None, q: str | None, limit: int):
        rows = self.repo.list_departamentos(campus_id=campus_id, unidade_id=unidade_id, q=q, limit=limit)
        return {"items": [dict(r) for r in rows]}

    def list_cursos(self, campus_id: int | None, unidade_id: int | None, q: str | None, limit: int, offset: int):
        rows = self.repo.list_cursos(campus_id=campus_id, unidade_id=unidade_id, q=q, limit=limit, offset=offset)
        return {"items": [dict(r) for r in rows], "limit": limit, "offset": offset}

    def list_disciplinas_by_curso(self, curso_id: int, limit: int):
        rows = self.repo.disciplinas_by_curso(curso_id=curso_id, limit=limit)
        return {"items": [dict(r) for r in rows]}

    def list_disciplinas(self, curso_id: int | None, unidade_id: int | None, campus_id: int | None, q: str | None, limit: int):
        rows = self.repo.list_disciplinas(curso_id=curso_id, unidade_id=unidade_id, campus_id=campus_id, q=q, limit=limit)
        return {"items": [dict(r) for r in rows]}

    def list_proreitorias(self, q: str | None, limit: int):
        rows = self.repo.list_proreitorias(q=q, limit=limit)
        return {"items": [dict(r) for r in rows]}