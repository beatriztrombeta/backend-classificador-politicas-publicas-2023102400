from datetime import datetime, timedelta
from jose import jwt, JWTError
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

    def generate_token(self, user_id: int, action: str, doc_id: int | None = None, expires_in_minutes: int | None = None) -> str:
        """
        action: 'approve', 'reject' ou 'view_doc'
        doc_id: obrigatório quando action='view_doc'
        expires_in_minutes: opcional para sobrescrever expiração (ex.: docs com expiração curta)
        """
        allowed_actions = ("approve", "reject", "view_doc")
        if action not in allowed_actions:
            raise ValueError("Invalid approval action")

        if action == "view_doc" and not doc_id:
            raise ValueError("doc_id is required for view_doc action")

        now = datetime.utcnow()
        if expires_in_minutes is not None:
            exp = now + timedelta(minutes=expires_in_minutes)
        else:
            exp = now + timedelta(hours=self.expiration_hours)

        payload = {
            "sub": str(user_id),
            "action": action,
            "type": "approval",
            "exp": exp,
            "iat": now,
        }

        if doc_id is not None:
            payload["doc_id"] = int(doc_id)

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise ExpiredApprovalTokenError("approval_token_expired")
        except JWTError:
            raise InvalidApprovalTokenError("invalid_approval_token")

        if payload.get("type") != "approval":
            raise InvalidApprovalTokenError("invalid_token_type")

        if payload.get("action") not in ("approve", "reject", "view_doc"):
            raise InvalidApprovalTokenError("invalid_action")

        doc_id = payload.get("doc_id")
        if payload.get("action") == "view_doc":
            if doc_id is None:
                raise InvalidApprovalTokenError("missing_doc_id")
            try:
                doc_id = int(doc_id)
            except (TypeError, ValueError):
                raise InvalidApprovalTokenError("invalid_doc_id")

        return {
            "user_id": int(payload.get("sub")),
            "action": payload.get("action"),
            "doc_id": doc_id if payload.get("action") == "view_doc" else None,
        }