from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.approval_token_service import ApprovalTokenService
from app.utils.email_templates import admin_document_review_email
from app.utils.email_service import EmailService
from app.repositories.user_repository import UserRepository
from app.config import settings


class AdminNotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.token_service = ApprovalTokenService()
        self.email_service = EmailService()
        self.frontend_url = settings.FRONTEND_URL
        self.backend_url = settings.BACKEND_URL

    def notify_pending_user(self, user_id: int):
        pending_user = UserRepository.get_by_id(self.db, user_id)
        if not pending_user:
            raise ValueError("Usuário não encontrado")

        if pending_user.status_cadastro != "PENDENTE":
            return

        admins = UserRepository.get_admin_users(self.db)
        if not admins:
            return

        approve_token = self.token_service.generate_token(user_id=pending_user.id_usuario, action="approve")
        reject_token  = self.token_service.generate_token(user_id=pending_user.id_usuario, action="reject")

        base = settings.BACKEND_URL.rstrip("/")
        approve_link = f"{base}/notify/admin/approval/approve?token={approve_token}"
        reject_link  = f"{base}/notify/admin/approval/reject?token={reject_token}"

        docs = self.db.execute(
            text("""
                SELECT id_documento, tipo_documento
                FROM documento_usuario
                WHERE id_usuario = :user_id
                ORDER BY id_documento
            """),
            {"user_id": pending_user.id_usuario},
        ).mappings().all()

        documents_links = []
        for d in docs:
            view_token = self.token_service.generate_token(
                user_id=pending_user.id_usuario,
                action="view_doc",
                doc_id=d["id_documento"],
                expires_in_minutes=60
            )
            view_link = f"{base}/notify/admin/document/view?token={view_token}"
            documents_links.append((d["tipo_documento"], view_link))

        for admin in admins:
            subject, body = admin_document_review_email(
                admin_name=admin.nome,
                user_name=pending_user.nome,
                user_email=pending_user.email,
                approve_link=approve_link,
                reject_link=reject_link,
                documents=documents_links,
            )

            self.email_service.send_email(
                to_email=admin.email,
                subject=subject,
                body=body,
            )
