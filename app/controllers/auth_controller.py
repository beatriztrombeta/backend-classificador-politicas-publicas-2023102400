from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import User
from app.utils.auth import generate_code, store_code, verify_code, create_jwt_token, register_failed_attempt, reset_attempts
from app.utils.email_service import send_email
from app.services.email_validation_service import (
    EmailValidationService,
    InvalidEmailError,
    InvalidInstitutionalDomainError
)

email_validation_service = EmailValidationService()

def send_login_code(email: str, db: Session):
    try:
        email_validation_service.validate(email)
    except InvalidEmailError:
        raise HTTPException(
            status_code=400,
            detail="Formato de e-mail inválido."
        )
    except InvalidInstitutionalDomainError:
        raise HTTPException(
            status_code=400,
            detail="Apenas e-mails institucionais são permitidos."
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    code = generate_code()
    store_code(email, code)
    send_email(email, "Seu código de verificação", f"Seu código é: {code}")

    return {"message": "Código enviado com sucesso."}

def validate_login_code(email: str, code: str):
    try:
        email_validation_service.validate(email)
    except (InvalidEmailError, InvalidInstitutionalDomainError):
        raise HTTPException(
            status_code=400,
            detail="E-mail inválido."
        )

    if not verify_code(email, code):
        register_failed_attempt(email)
        raise HTTPException(status_code=401, detail="Código inválido ou expirado.")

    reset_attempts(email)
    token = create_jwt_token(email)

    return {"access_token": token}

