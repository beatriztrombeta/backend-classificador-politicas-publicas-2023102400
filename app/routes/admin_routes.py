from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/pending-users")
def pending_users(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
    limit: int = Query(200, ge=1, le=1000),
):
    rows = db.execute(
        text("""
            SELECT id_usuario, nome, email, status_cadastro, data_cadastro
            FROM usuario
            WHERE status_cadastro = 'PENDENTE'
            ORDER BY data_cadastro ASC
            LIMIT :limit
        """),
        {"limit": limit},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
    status: str | None = Query(
        None,
        description="PENDENTE | APROVADO | REJEITADO"
    ),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0, le=200000),
):
    where = []
    params = {"limit": limit, "offset": offset}

    if status:
        where.append("status_cadastro = :status")
        params["status"] = status

    sql = f"""
        SELECT id_usuario, id_categoria_usuario, nome, email, status_cadastro, data_cadastro, data_atualizacao
        FROM usuario
        {"WHERE " + " AND ".join(where) if where else ""}
        ORDER BY data_cadastro DESC
        LIMIT :limit OFFSET :offset
    """
    rows = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(r) for r in rows], "limit": limit, "offset": offset}


# (Opcional) detalhe do usuário para tela admin
@router.get("/users/{user_id}")
def get_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
):
    row = db.execute(
        text("""
            SELECT id_usuario, id_categoria_usuario, nome, email, cpf, telefone,
                   status_cadastro, data_cadastro, data_atualizacao
            FROM usuario
            WHERE id_usuario = :uid
            LIMIT 1
        """),
        {"uid": user_id},
    ).mappings().first()
    return {"data": dict(row) if row else None}