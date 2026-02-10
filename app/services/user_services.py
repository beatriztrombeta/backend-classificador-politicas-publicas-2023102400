from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from typing import Union
from app.schemas.user_schema import (
    UserCreate, UserAluno, UserProfessor, UserCoordenacao,
    UserDepartamento, UserProReitor, UserReitor, CategoriaEnum,
    UserCreateResponse, SavedFile, DuplicatedDisciplinaError, DisciplinaNotFoundError,
    CursoNotFoundError, DepartamentoNotFoundError, CategoriaNotFoundError,
    UnidadeNotFoundError, CampusNotFoundError, AlunoNotFoundError
)
from app.repositories.user_repository import UserRepository
from app.models.user_model import StatusCadastroEnum
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
            CategoriaEnum.REITORIA: self.repository.create_usuario_reitor
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
        # Verifica se o email já existe
        if self.repository.email_exists(db, user_data.email):
            raise HTTPException(
                status_code=409, 
                detail="A user with this email address already exists."
            )
        
        try:
            # Cria o usuário base
            base_user = self.repository.create_base_user(
                db=db,
                user_data=user_data,
                categoria=user_data.categoria
            )
            
            # Cria o registro específico do tipo de usuário
            creator_function = self._get_user_creator_function(user_data.categoria)
            created_user = creator_function(db, user_data, base_user)
            
            # Valida e salva o arquivo
            await self.file_service.validate_file(file)
            saved_file = await self.file_service.save_file(file)
            
            # Cria o registro do documento
            self.repository.create_documento_usuario(
                db=db,
                saved_file=saved_file,
                usuario_id=created_user.id_usuario
            )

            db.commit()
            
            # Prepara a resposta
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

        except Exception:
            db.rollback()
            raise