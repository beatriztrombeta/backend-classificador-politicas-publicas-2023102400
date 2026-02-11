from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
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

def view_user_document(token: str, db: Session):
    token_service = ApprovalTokenService()

    try:
        token_data = token_service.validate_token(token)
    except ExpiredApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except InvalidApprovalTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")

    if token_data.get("action") != "view_doc":
        raise HTTPException(status_code=400, detail="Ação inválida para este token")

    user_id = token_data.get("user_id")
    doc_id = token_data.get("doc_id")
    if not user_id or not doc_id:
        raise HTTPException(status_code=400, detail="Token incompleto")

    row = db.execute(
        text("""
            SELECT storage_key, COALESCE(mime_type, 'application/octet-stream') AS mime_type
            FROM documento_usuario
            WHERE id_usuario = :user_id AND id_documento = :doc_id
            LIMIT 1
        """),
        {"user_id": user_id, "doc_id": doc_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    storage_key = row["storage_key"]
    mime_type = row["mime_type"]

    base_dir = Path(getattr(settings, "DOCUMENTS_BASE_DIR", "app/storage/documents")).resolve()
    file_path = Path(storage_key)

    if not file_path.is_absolute():
        file_path = (base_dir / file_path).resolve()
    else:
        file_path = file_path.resolve()

    if base_dir not in file_path.parents and file_path != base_dir:
        raise HTTPException(status_code=403, detail="Acesso ao arquivo negado")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage")

    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=file_path.name,
        headers={"Content-Disposition": f'inline; filename="{file_path.name}"'}
    )