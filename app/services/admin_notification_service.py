from sqlalchemy.orm import Session

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

    def notify_pending_user(self, user_id: int):
        pending_user = UserRepository.get_by_id(self.db, user_id)

        if not pending_user:
            raise ValueError("Usuário não encontrado")

        if pending_user.status_cadastro != "PENDENTE":
            return

        admins = UserRepository.get_admin_users(self.db)
        if not admins:
            return

        approve_token = self.token_service.generate_token(
            user_id=pending_user.id_usuario,
            action="approve"
        )

        reject_token = self.token_service.generate_token(
            user_id=pending_user.id_usuario,
            action="reject"
        )

        approve_link = f"{self.frontend_url}/admin/approval/approve?token={approve_token}"
        reject_link = f"{self.frontend_url}/admin/approval/reject?token={reject_token}"

        for admin in admins:
            subject, body = admin_document_review_email(
                admin_name=admin.nome,
                user_name=pending_user.nome,
                user_email=pending_user.email,
                approve_link=approve_link,
                reject_link=reject_link
            )

            self.email_service.send_email(
                to_email=admin.email,
                subject=subject,
                body=body
            )