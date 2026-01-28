import random
from fastapi import HTTPException, status, Cookie
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import settings

verification_codes = {}
security = HTTPBearer()
failed_attempts = {}

MAX_ATTEMPTS = 5
BLOCK_TIME_MINUTES = 10

def generate_code():
    return str(random.randint(100000, 999999))

def store_code(email: str, code: str):
    verification_codes[email] = {"code": code, "expires": datetime.utcnow() + timedelta(minutes=10)}

def verify_code(email: str, code: str):
    entry = verification_codes.get(email)
    if not entry or entry["expires"] < datetime.utcnow():
        return False
    return entry["code"] == code

def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(hours=2)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(token: str = Cookie(None)):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não encontrado.")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        exp: int = payload.get("exp")
        if email is None or exp < datetime.utcnow().timestamp():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    return {"email": email}

def register_failed_attempt(email: str):
    now = datetime.utcnow()
    entry = failed_attempts.get(email, {"count": 0, "blocked_until": None})

    if entry["blocked_until"] and entry["blocked_until"] > now:
        raise HTTPException(
            status_code=429,
            detail=f"Tentativas excessivas. Tente novamente após {entry['blocked_until']}."
        )

    entry["count"] += 1

    if entry["count"] >= MAX_ATTEMPTS:
        entry["blocked_until"] = now + timedelta(minutes=BLOCK_TIME_MINUTES)
        failed_attempts[email] = entry
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas. Aguarde {BLOCK_TIME_MINUTES} minutos."
        )

    failed_attempts[email] = entry


def reset_attempts(email: str):
    if email in failed_attempts:
        del failed_attempts[email]