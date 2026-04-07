from fastapi import Depends, UploadFile, File, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import TypeAdapter, ValidationError
from typing import List
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateForm, UserCreate, UserCreateResponse, UserResponse, DocumentResponse, UpdateStatusCadastro
from app.services.user_services import UserService
from app.utils.email_service import EmailService
from app.services.email_validation_service import (
    EmailValidationService,
    InvalidEmailError,
    InvalidInstitutionalDomainError,
)
from app.utils.auth import (
    generate_code,
    store_code,
    verify_code,
    register_failed_attempt,
    reset_attempts,
    create_signup_token,
)

class UserController:
    
    def __init__(self):
        self.service = UserService()
        self.email_validation_service = EmailValidationService()
        self.email_service = EmailService()
    
    async def create_new_user(
        self,
        form: UserCreateForm,
        file: UploadFile,
        db: Session
    ) -> UserCreateResponse:
        """
        Controller para criação de novo usuário
        """
        data = {k: v for k, v in vars(form).items() if v is not None}

        try:
            user_data = TypeAdapter(UserCreate).validate_python(data)
        except ValidationError as e:
            errors = e.errors()
            first_error = errors[0] if errors else None

            message = "Dados inválidos."
            if first_error:
                message = first_error.get("msg") or message

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=message,
            )

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
    
    def send_signup_code(self, email: str, db: Session):
        try:
            self.email_validation_service.validate(email)
        except InvalidEmailError:
            raise HTTPException(status_code=400, detail="Formato de e-mail inválido.")
        except InvalidInstitutionalDomainError:
            raise HTTPException(status_code=400, detail="Apenas e-mails institucionais são permitidos.")

        if UserRepository.email_exists(db, email):
            raise HTTPException(status_code=409, detail="A user with this email address already exists.")

        code = generate_code()
        store_code(email, code)

        self.email_service.send_email(
            email,
            "Seu código de verificação (cadastro)",
            f"Seu código é: {code}"
        )

        return {"message": "Código enviado com sucesso."}

    def verify_signup_code(self, email: str, code: str, response: Response, db: Session):
        try:
            self.email_validation_service.validate(email)
        except (InvalidEmailError, InvalidInstitutionalDomainError):
            raise HTTPException(status_code=400, detail="E-mail inválido.")

        if UserRepository.email_exists(db, email):
            raise HTTPException(status_code=409, detail="A user with this email address already exists.")

        if not verify_code(email, code):
            register_failed_attempt(email)
            raise HTTPException(status_code=401, detail="Código inválido ou expirado.")

        reset_attempts(email)

        signup_token = create_signup_token(email)

        response.set_cookie(
            key="signup_token",
            value=signup_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=20 * 60
        )

        return {"message": "E-mail verificado com sucesso."}
