from sqlalchemy.orm import Session
from pathlib import Path
from app.config import settings
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.schemas.user_schema import (
    UserCreate, UserAluno, UserProfessor, UserCoordenacao,
    UserDepartamento, UserProReitor, UserReitor, CategoriaEnum, SavedFile, DuplicatedDisciplinaError, DisciplinaNotFoundError,
    CursoNotFoundError, DepartamentoNotFoundError, CategoriaNotFoundError,
    UnidadeNotFoundError, CampusNotFoundError, AlunoNotFoundError,
    UserCreateResponse, UpdateStatusCadastro, UpdateStatusCadastroResponse,EmptyDisciplinaListError
)
from app.repositories.user_repository import UserRepository
from app.models.user_model import StatusCadastroEnum, DocumentoUsuario
from app.services.file_service import FileService

class UserService:
    
    def __init__(self):
        self.repository = UserRepository()
        self.file_service = FileService()
    
    def _get_user_creator_function(self, categoria: CategoriaEnum):
        """Retorna a função adequada para criar o usuário específico baseado na categoria"""
        user_creators = {
            CategoriaEnum.ALUNO: self.repository.create_usuario_aluno,
            CategoriaEnum.PROFESSOR: self.repository.create_usuario_professor,
            CategoriaEnum.COORDENACAO: self.repository.create_usuario_coordenador,
            CategoriaEnum.DEPARTAMENTO: self.repository.create_usuario_departamento,
            CategoriaEnum.PRO_REITORIA: self.repository.create_usuario_pro_reitor,
            CategoriaEnum.REITORIA: self.repository.create_usuario_reitor,
            CategoriaEnum.ADMIN: self.repository.create_usuario_admin
        }
        return user_creators.get(categoria)
    
    async def create_user(
        self, 
        db: Session, 
        user_data: UserCreate,
        file: UploadFile
    ) -> UserCreateResponse:
        """
        Cria um novo usuário no sistema
        
        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário a ser criado
            file: Arquivo PDF de comprovante
            
        Returns:
            UserCreateResponse com dados do usuário criado
            
        Raises:
            HTTPException: Em caso de erro na validação ou criação
        """
        if self.repository.email_exists(db, user_data.email):
            raise HTTPException(
                status_code=409, 
                detail="A user with this email address already exists."
            )
        
        try:
            base_user = self.repository.create_base_user(
                db=db,
                user_data=user_data,
                categoria=user_data.categoria
            )
            
            creator_function = self._get_user_creator_function(user_data.categoria)
            created_user = creator_function(db, user_data, base_user)
            
            await self.file_service.validate_file(file)
            saved_file = await self.file_service.save_file(
                file=file,
                subdir=f"users/{base_user.id_usuario}"
            )

            self.repository.create_documento_usuario(
                db=db,
                saved_file=saved_file,
                usuario_id=created_user.id_usuario
            )

            db.commit()
            
            return UserCreateResponse(
                id=created_user.id_usuario,
                email=user_data.email,
                status=StatusCadastroEnum.PENDENTE
            )
        
        except DisciplinaNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Disciplina informada não existe"
            )
        
        except DuplicatedDisciplinaError:
            raise HTTPException(
                status_code=409,
                detail="Foram informadas disciplinas duplicadas"
            )
        
        except CursoNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Curso informado não existe"
            )

        except DepartamentoNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Departamento informado não existe"
            )

        except CategoriaNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Categoria informada não existe"
            )

        except UnidadeNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Unidade informada não existe"
            )
        
        except CampusNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Campus informado não existe"
            )
        
        except AlunoNotFoundError:
            raise HTTPException(
                status_code=400,
                detail="Aluno informado não existe"
            )
        
        except EmptyDisciplinaListError:
            raise HTTPException(
                status_code=400,
                detail="Professor deve informar ao menos uma disciplina"
    )

        except Exception:
            db.rollback()
            raise

    async def list_pending_users(self, db: Session):
        return self.repository.list_pending_users(db)
    
    async def list_documents(self, db: Session):
        return self.repository.list_documents(db)
    
    def download_document(self, document_id: int, db: Session):
        document = (
            db.query(DocumentoUsuario)
            .filter(DocumentoUsuario.id_documento == document_id)
            .first()
        )

        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        raw_path = Path(document.storage_key)
        if raw_path.is_absolute():
            raise HTTPException(status_code=500, detail="storage_key absoluto não é permitido")

        base_dir = Path(getattr(settings, "DOCUMENTS_BASE_DIR", "app/storage/documents")).resolve()
        file_path = (base_dir / raw_path).resolve()

        if base_dir not in file_path.parents and file_path != base_dir:
            raise HTTPException(status_code=403, detail="Acesso ao arquivo negado")

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        return FileResponse(
            path=str(file_path),
            media_type=document.mime_type,
            filename=file_path.name
        )

    def approval_reject_registration(self, body: UpdateStatusCadastro, id: int, db: Session):
        try:
            user = self.repository.update_status(user_id=id, new_status=body.status, db=db)
        except ValueError:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return UpdateStatusCadastroResponse(id=user.id_usuario, nome=user.nome, email=user.email, status=user.status_cadastro)
