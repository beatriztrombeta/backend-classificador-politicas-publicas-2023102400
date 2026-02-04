from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.approval_token_service import (
    ApprovalTokenService,
    InvalidApprovalTokenError,
    ExpiredApprovalTokenError
)
from app.repositories.user_repository import UserRepository
from app.utils.email_service import EmailService
from app.utils.email_templates import user_approval_email, user_rejection_email
from app.config import settings


def approve_user(token: str, db: Session):
    token_service = ApprovalTokenService()
    email_service = EmailService()

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

    login_url = settings.FRONTEND_URL
    subject, body = user_approval_email(
        user_name=user.nome,
        login_url=login_url
    )
    
    email_service.send_email(
        to_email=user.email,
        subject=subject,
        body=body
    )

    return {"message": "Usuário aprovado com sucesso."}


def reject_user(token: str, db: Session):
    token_service = ApprovalTokenService()
    email_service = EmailService()

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

    contact_email = getattr(settings, 'SUPPORT_EMAIL', 'suporte@unesp.br')  # Email de suporte
    subject, body = user_rejection_email(
        user_name=user.nome,
        contact_email=contact_email
    )
    
    email_service.send_email(
        to_email=user.email,
        subject=subject,
        body=body
    )

    return {"message": "Usuário rejeitado com sucesso."}