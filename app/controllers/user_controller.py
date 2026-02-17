from fastapi import Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import TypeAdapter
from app.schemas.user_schema import UserCreateForm, UserCreate, UserCreateResponse, UserResponse, DocumentResponse, UpdateStatusCadastro
from app.services.user_services import UserService
from typing import List
from datetime import datetime
from app.services.email_validation_service import (
    EmailValidationService,
    InvalidEmailError,
    InvalidInstitutionalDomainError,
)

class UserController:
    
    def __init__(self):
        self.service = UserService()
        self.email_validation_service = EmailValidationService()
    
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
        data = {k: v for k, v in vars(form).items() if v is not None}
        user_data = TypeAdapter(UserCreate).validate_python(data)

        try:
            self.email_validation_service.validate(user_data.email)
        except (InvalidEmailError, InvalidInstitutionalDomainError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        result = await self.service.create_user(
            db=db,
            user_data=user_data,
            file=file
        )
        return result

    async def list_pending_users(self, db: Session) -> List[UserResponse]:
        users = await self.service.list_pending_users(db)

        res = [UserResponse(id=user.id_usuario, nome=user.nome, email=user.email) for user in users]

        return res
    
    async def list_documents(self, db: Session) -> List[DocumentResponse]:
        documents = await self.service.list_documents(db)

        print(documents, type(documents[0].data_envio))

        res = [DocumentResponse(
            id_documento=doc.id_documento,
            id_usuario=doc.id_usuario,
            tipo_documento=doc.tipo_documento,
            tamanho_arquivo=doc.tamanho_arquivo,
            data_envio=doc.data_envio,
            status_analise=doc.status_analise,
        ) for doc in documents]

        return res
    
    def download_document(self, document_id: int, db: Session):
        return self.service.download_document(document_id, db)
    
    def approval_reject_registration(self, body: UpdateStatusCadastro, id: int, db: Session):
        return self.service.approval_reject_registration(body, id, db)
