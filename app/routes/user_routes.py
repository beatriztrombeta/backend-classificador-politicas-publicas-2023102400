from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user_schema import UserCreateForm, UserCreateResponse, UserResponse, DocumentResponse, UpdateStatusCadastro
from app.controllers.user_controller import UserController
from typing import List

router = APIRouter(prefix="/users", tags=["Usuários"])

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

@router.get("/pendings", response_model=List[UserResponse])
async def list_pending_users(db: Session = Depends(get_db)):
    return await user_controller.list_pending_users(db)

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    return await user_controller.list_documents(db)

@router.get("/documents/download/{document_id}")
def download_document(document_id: int, db: Session = Depends(get_db)):
    return user_controller.download_document(document_id, db)

@router.patch("/status/{id}")
def approval_reject_registration(body: UpdateStatusCadastro, id: int, db: Session = Depends(get_db)):
    return user_controller.approval_reject_registration(body, id, db)