from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.approval_token_service import (
    ApprovalTokenService,
    InvalidApprovalTokenError,
    ExpiredApprovalTokenError
)
from app.repositories.user_repository import UserRepository


def approve_user(token: str, db: Session):
    token_service = ApprovalTokenService()

    try:
        token_data = token_service.validate_token(token)
    except ExpiredApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except InvalidApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")

    if token_data["action"] != "approve":
        raise HTTPException(status_code=400, detail="Ação inválida para este token")

    user = UserRepository.get_by_id(db, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.status_cadastro != "PENDENTE":
        raise HTTPException(status_code=400, detail="Usuário já analisado")

    UserRepository.update_status(db, user.id_usuario, "APROVADO")

    return {"message": "Usuário aprovado com sucesso."}


def reject_user(token: str, db: Session):
    token_service = ApprovalTokenService()

    try:
        token_data = token_service.validate_token(token)
    except ExpiredApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except InvalidApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")

    if token_data["action"] != "reject":
        raise HTTPException(status_code=400, detail="Ação inválida para este token")

    user = UserRepository.get_by_id(db, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.status_cadastro != "PENDENTE":
        raise HTTPException(status_code=400, detail="Usuário já analisado")

    UserRepository.update_status(db, user.id_usuario, "REJEITADO")

    return {"message": "Usuário rejeitado com sucesso."}