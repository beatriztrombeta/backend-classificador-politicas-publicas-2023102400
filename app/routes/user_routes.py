from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user_schema import UserCreateForm, UserCreateResponse, CategoriaEnum
from app.controllers.user_controller import UserController

router = APIRouter(prefix="/users", tags=["users"])

user_controller = UserController()

@router.post("", response_model=UserCreateResponse)
async def create_new_user(
    form: UserCreateForm = Depends(UserCreateForm.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo usuário
    
    Args:
        form: Dados do formulário de criação de usuário
        file: Arquivo PDF de comprovante
        db: Sessão do banco de dados
        
    Returns:
        UserCreateResponse com dados do usuário criado
    """
    return await user_controller.create_new_user(
        form=form,
        file=file,
        db=db
    )
