from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.access_control import require_permission
from app.schemas.permission_schema import Resource, Action, AccessScope
from app.controllers.admin_controller import (
    AdminController,
    approve_user_internal,
    reject_user_internal,
    view_user_document_internal,
    list_user_documents_internal,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

admin_controller = AdminController()

@router.get("/pending-users")
def pending_users(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
    limit: int = Query(200, ge=1, le=1000),
):
    return admin_controller.list_pending_users(db=db, limit=limit)

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
    return admin_controller.list_users(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )

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

@router.post("/users/{user_id}/approve")
def approve_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
):
    return approve_user_internal(user_id=user_id, db=db)

@router.post("/users/{user_id}/reject")
def reject_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
):
    return reject_user_internal(user_id=user_id, db=db)

@router.get("/users/{user_id}/documents")
def list_user_documents_admin(
    user_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
):
    return list_user_documents_internal(user_id=user_id, db=db)


@router.get("/users/{user_id}/documents/{doc_id}/view")
def view_user_document_admin(
    user_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(require_permission(Resource.USER_MGMT, Action.MANAGE)),
):
    return view_user_document_internal(user_id=user_id, doc_id=doc_id, db=db)