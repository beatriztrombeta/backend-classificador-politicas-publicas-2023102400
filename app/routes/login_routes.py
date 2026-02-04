from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.controllers.auth_controller import (
    send_login_code,
    validate_login_code
)
from app.schemas.login_schema import UserLogin, VerifyCode
from app.controllers.admin_controller import (
    approve_user,
    reject_user
)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/send-code")
def send_code(data: UserLogin, db: Session = Depends(get_db)):
    return send_login_code(data.email, db)

@router.post("/verify-code")
def verify_code_endpoint(data: VerifyCode, response: Response):
    token_data = validate_login_code(data.email, data.code)
    token = token_data.get("access_token")

    if not token:
        raise HTTPException(status_code=500, detail="Falha ao gerar token JWT.")

    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=3600
    )

    return {"message": "Login bem-sucedido."}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logout realizado com sucesso."}