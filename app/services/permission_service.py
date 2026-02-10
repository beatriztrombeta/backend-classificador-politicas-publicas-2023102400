from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.schemas.permission_schema import RoleId, Resource, Action, AccessScope

class PermissionService:
    PERMISSIONS = {
        RoleId.ADMIN: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
            (Resource.REPORTS, Action.READ),
            (Resource.USER_MGMT, Action.MANAGE),
        },
        RoleId.REITORIA: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
            (Resource.REPORTS, Action.READ),
        },
        RoleId.PRO_REITORIA: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
            (Resource.REPORTS, Action.READ),
        },
        RoleId.DEPARTAMENTO: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
            (Resource.REPORTS, Action.READ),
        },
        RoleId.COORDENACAO: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
            (Resource.REPORTS, Action.READ),
        },
        RoleId.PROFESSOR: {
            (Resource.STUDENT, Action.READ),
            (Resource.STUDENT_LIST, Action.LIST),
        },
        RoleId.ALUNO: {
            (Resource.STUDENT, Action.READ),
        },
    }

    def can(self, role_id: RoleId, resource: Resource, action: Action) -> bool:
        if role_id == RoleId.ADMIN:
            return True
        return (resource, action) in self.PERMISSIONS.get(role_id, set())

    def assert_allowed(self, scope: AccessScope, resource: Resource, action: Action):
        if not self.can(scope.role_id, resource, action):
            raise HTTPException(status_code=403, detail="Not allowed for this role")

    def build_scope(self, db: Session, user_id: int) -> AccessScope:
        row = db.execute(
            text("SELECT id_categoria_usuario FROM usuario WHERE id_usuario = :uid"),
            {"uid": user_id},
        ).mappings().first()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        role_id = RoleId(int(row["id_categoria_usuario"]))
        scope = AccessScope(role_id=role_id, user_id=user_id)

        if role_id == RoleId.ADMIN:
            return scope

        if role_id == RoleId.REITORIA:
            rows = db.execute(
                text("SELECT id_campus FROM usuario_reitor WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.campus_ids.add(int(r["id_campus"]))

            if scope.campus_ids:
                urows = db.execute(
                    text("SELECT id_unidade FROM unidade WHERE id_campus = ANY(:cids)"),
                    {"cids": list(scope.campus_ids)},
                ).mappings().all()
                for r in urows:
                    scope.unidade_ids.add(int(r["id_unidade"]))

            return scope

        if role_id == RoleId.PRO_REITORIA:
            rows = db.execute(
                text("SELECT id_campus, id_proreitoria FROM usuario_prorei WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.campus_ids.add(int(r["id_campus"]))
                scope.proreitoria_ids.add(int(r["id_proreitoria"]))

            if scope.campus_ids:
                urows = db.execute(
                    text("SELECT id_unidade FROM unidade WHERE id_campus = ANY(:cids)"),
                    {"cids": list(scope.campus_ids)},
                ).mappings().all()
                for r in urows:
                    scope.unidade_ids.add(int(r["id_unidade"]))

            return scope

        if role_id == RoleId.DEPARTAMENTO:
            rows = db.execute(
                text("SELECT id_unidade, id_departamento FROM usuario_departamento WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.unidade_ids.add(int(r["id_unidade"]))
                scope.departamento_ids.add(int(r["id_departamento"]))

            if scope.unidade_ids:
                crows = db.execute(
                    text("SELECT id_curso FROM curso WHERE id_unidade = ANY(:uids)"),
                    {"uids": list(scope.unidade_ids)},
                ).mappings().all()
                for r in crows:
                    scope.curso_ids.add(int(r["id_curso"]))

            return scope

        if role_id == RoleId.COORDENACAO:
            rows = db.execute(
                text("SELECT id_unidade, id_curso FROM usuario_coordenador WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.unidade_ids.add(int(r["id_unidade"]))
                scope.curso_ids.add(int(r["id_curso"]))
            return scope

        if role_id == RoleId.PROFESSOR:
            rows = db.execute(
                text("SELECT id_unidade, id_disciplina FROM usuario_professor WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.unidade_ids.add(int(r["id_unidade"]))
                scope.disciplina_ids.add(int(r["id_disciplina"]))

            if scope.disciplina_ids:
                crows = db.execute(
                    text("SELECT DISTINCT id_curso FROM disciplina WHERE id_disciplina = ANY(:dids)"),
                    {"dids": list(scope.disciplina_ids)},
                ).mappings().all()
                for r in crows:
                    scope.curso_ids.add(int(r["id_curso"]))

            return scope

        if role_id == RoleId.ALUNO:
            rows = db.execute(
                text("SELECT id_unidade, id_aluno_graduacao FROM usuario_aluno WHERE id_usuario = :uid"),
                {"uid": user_id},
            ).mappings().all()
            for r in rows:
                scope.unidade_ids.add(int(r["id_unidade"]))
                scope.aluno_ids.add(int(r["id_aluno_graduacao"]))
            return scope

        return scope

    def assert_student_access(self, db: Session, scope: AccessScope, aluno_id: int):
        if scope.role_id == RoleId.ALUNO:
            if aluno_id not in scope.aluno_ids:
                raise HTTPException(status_code=403, detail="Aluno só pode acessar seus próprios dados")
            return

        if scope.role_id == RoleId.ADMIN:
            return

        row = db.execute(
            text("""
                SELECT a.id_curso, c.id_unidade, u.id_campus
                FROM aluno a
                JOIN curso c ON c.id_curso = a.id_curso
                JOIN unidade u ON u.id_unidade = c.id_unidade
                WHERE a.id_aluno_graduacao = :aid
            """),
            {"aid": aluno_id},
        ).mappings().first()

        if not row:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")

        id_curso = int(row["id_curso"])
        id_unidade = int(row["id_unidade"])
        id_campus = int(row["id_campus"])

        if scope.role_id in (RoleId.REITORIA, RoleId.PRO_REITORIA):
            if scope.campus_ids and id_campus not in scope.campus_ids:
                raise HTTPException(status_code=403, detail="Fora do escopo do campus")
            if not scope.campus_ids and scope.unidade_ids and id_unidade not in scope.unidade_ids:
                raise HTTPException(status_code=403, detail="Fora do escopo da unidade")
            return

        if scope.role_id in (RoleId.DEPARTAMENTO, RoleId.COORDENACAO):
            if scope.curso_ids and id_curso not in scope.curso_ids:
                raise HTTPException(status_code=403, detail="Fora do escopo do curso")
            return

        if scope.role_id == RoleId.PROFESSOR:
            if not scope.disciplina_ids:
                raise HTTPException(status_code=403, detail="Professor sem disciplinas vinculadas")
            ok = db.execute(
                text("""
                    SELECT 1
                    FROM aluno_disciplina ad
                    WHERE ad.id_aluno_graduacao = :aid
                      AND ad.id_disciplina = ANY(:dids)
                    LIMIT 1
                """),
                {"aid": aluno_id, "dids": list(scope.disciplina_ids)},
            ).first()
            if not ok:
                raise HTTPException(status_code=403, detail="Fora do escopo (disciplina)")
            return

        raise HTTPException(status_code=403, detail="Escopo não atendido")