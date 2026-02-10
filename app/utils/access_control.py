from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.permission_service import PermissionService
from app.schemas.permission_schema import Resource, Action, AccessScope
from app.utils.auth import get_current_user

from app.models.user_model import User  # <- necessário para lookup por email

permission_service = PermissionService()

def _resolve_user_id(db: Session, current_user) -> int:
    if hasattr(current_user, "id_usuario") and current_user.id_usuario is not None:
        return int(current_user.id_usuario)

    if isinstance(current_user, dict):
        # chaves comuns
        for key in ("id_usuario", "user_id", "id", "uid"):
            if key in current_user and current_user[key] is not None:
                try:
                    return int(current_user[key])
                except (TypeError, ValueError):
                    pass

        email = current_user.get("email") or current_user.get("sub")
        if email:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=401, detail="Usuário não encontrado para o token atual.")
            return int(user.id_usuario)

    raise HTTPException(status_code=401, detail="Token inválido: não foi possível identificar o usuário.")

def get_access_scope(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AccessScope:
    user_id = _resolve_user_id(db, current_user)
    return permission_service.build_scope(db=db, user_id=user_id)

def require_permission(resource: Resource, action: Action):
    """
    Garante RBAC (papel pode fazer ação no recurso).
    O escopo (campus/unidade/curso/...) é checado em asserts específicos.
    """
    def _dep(scope: AccessScope = Depends(get_access_scope)) -> AccessScope:
        permission_service.assert_allowed(scope, resource, action)
        return scope
    return _dep
