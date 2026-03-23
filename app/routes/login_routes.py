from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user_model import User
from app.controllers.auth_controller import (
    send_login_code,
    validate_login_code
)
from app.schemas.login_schema import UserLogin, VerifyCode

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/send-code")
def send_code(data: UserLogin, db: Session = Depends(get_db)):
    return send_login_code(data.email, db)

@router.post("/verify-code")
def verify_code_endpoint(data: VerifyCode, response: Response, db: Session = Depends(get_db)):
    token_data = validate_login_code(data.email, data.code, db)
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

    return {
        "message": "Login bem-sucedido.",
        "id_categoria_usuario": token_data.get("id_categoria_usuario"),
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logout realizado com sucesso."}

@router.get("/me")
def me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    return {
        "email": user.email,
        "id_usuario": getattr(user, "id_usuario", None),
        "id_categoria_usuario": getattr(user, "id_categoria_usuario", None),
        "nome": getattr(user, "nome", None),
        "status_cadastro": str(getattr(user, "status_cadastro", "")),
    }