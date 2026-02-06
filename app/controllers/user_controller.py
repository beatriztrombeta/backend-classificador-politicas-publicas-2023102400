from fastapi import Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import TypeAdapter
from app.schemas.user_schema import UserCreateForm, UserCreate, UserCreateResponse
from app.services.user_services import UserService

class UserController:
    
    def __init__(self):
        self.service = UserService()
    
    async def create_new_user(
        self,
        form: UserCreateForm,
        file: UploadFile,
        db: Session
    ) -> UserCreateResponse:
        """
        Controller para criação de novo usuário
        
        Args:
            form: Dados do formulário
            file: Arquivo PDF enviado
            db: Sessão do banco de dados
            
        Returns:
            UserCreateResponse com dados do usuário criado
        """
        try:
            # Converte os dados do formulário para o schema apropriado
            data = {k: v for k, v in vars(form).items() if v is not None}
            user_data = TypeAdapter(UserCreate).validate_python(data)
            
            # Delega a criação para o service
            result = await self.service.create_user(
                db=db,
                user_data=user_data,
                file=file
            )
            
            # Commit da transação
            db.commit()
            
            return result
            
        except Exception:
            # Rollback em caso de erro
            db.rollback()
            raise
