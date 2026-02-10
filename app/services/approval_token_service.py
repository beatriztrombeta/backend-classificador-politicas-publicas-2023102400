from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

class InvalidApprovalTokenError(Exception):
    pass

class ExpiredApprovalTokenError(Exception):
    pass

class ApprovalTokenService:
    def __init__(self):
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = 24

    def generate_token(self, user_id: int, action: str) -> str:
        """
        action: 'approve' ou 'reject'
        """
        if action not in ("approve", "reject"):
            raise ValueError("Invalid approval action")

        payload = {
            "sub": str(user_id),
            "action": action,
            "type": "approval",
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredApprovalTokenError("approval_token_expired")
        except JWTError:
            raise InvalidApprovalTokenError("invalid_approval_token")

        if payload.get("type") != "approval":
            raise InvalidApprovalTokenError("invalid_token_type")

        if payload.get("action") not in ("approve", "reject"):
            raise InvalidApprovalTokenError("invalid_action")

        return {
            "user_id": int(payload.get("sub")),
            "action": payload.get("action"),
        }