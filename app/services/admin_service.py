from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository

class AdminService:
    def __init__(self):
        self.repository = UserRepository()

    def list_pending_users(self, db: Session, limit: int):
        return self.repository.list_pending_users_admin(db=db, limit=limit)
    
    def list_users(self, db: Session, status: str | None, limit: int, offset: int):
        return self.repository.list_users_admin(
            db=db,
            status=status,
            limit=limit,
            offset=offset,
        )