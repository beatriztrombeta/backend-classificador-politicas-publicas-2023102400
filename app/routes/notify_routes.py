from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db

from app.controllers.admin_controller import (
    approve_user,
    reject_user,
    view_user_document
)

router = APIRouter(prefix="/notify", tags=["Notify"])

@router.get("/admin/approval/approve")
def approve_user_route(token: str, db: Session = Depends(get_db)):
    return approve_user(token, db)


@router.get("/admin/approval/reject")
def reject_user_route(token: str, db: Session = Depends(get_db)):
    return reject_user(token, db)

@router.get("/admin/document/view")
def view_user_document_route(token: str, db: Session = Depends(get_db)):
    return view_user_document(token, db)

@router.post("/admin/notify-pending/{user_id}")
def notify_admin(user_id: int, db: Session = Depends(get_db)):
    from app.services.admin_notification_service import AdminNotificationService

    service = AdminNotificationService(db)
    service.notify_pending_user(user_id)

    return {"message": "Admins notificados com sucesso."}