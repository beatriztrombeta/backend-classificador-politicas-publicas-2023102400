from sqlalchemy.orm import Session
from typing import Optional, Union
from app.models.user_model import (
    User, Unidade, UserAluno, UserProfessor, 
    UserCoordenador, UserDepartamento, DocumentoUsuario,
    StatusCadastroEnum, StatusAnaliseEnum
)
from app.schemas.user_schema import (
    UserBase, UserAluno as UserAlunoSchema, 
    UserProfessor as UserProfessorSchema,
    UserCoordenacao as UserCoordenacaoSchema,
    UserDepartamento as UserDepartamentoSchema,
    UserProReitor as UserProReitorSchema,
    UserReitor as UserReitorSchema,
    CategoriaEnum, SavedFile
)

class UserRepository:
    
    @staticmethod
    def get_unidade_by_id(db: Session, unidade_id: int) -> Optional[Unidade]:
        """Busca uma unidade pelo ID"""
        return db.query(Unidade).filter(Unidade.id_unidade == unidade_id).first()
    
    @staticmethod
    def email_exists(db: Session, email: str) -> bool:
        """Verifica se um email já está cadastrado"""
        return db.query(User).filter(User.email == email).first() is not None
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Busca um usuário pelo ID"""
        return db.query(User).filter(User.id_usuario == user_id).first()
    
    @staticmethod
    def get_admin_users(db: Session) -> list[User]:
        """Busca todos os usuários administradores (categoria_usuario = 1)"""
        # NOTA: Ajuste o valor '1' conforme o ID da categoria admin no seu banco
        return db.query(User).filter(User.id_categoria_usuario == 1).all()
    
    @staticmethod
    def update_status(db: Session, user_id: int, new_status: str):
        """Atualiza o status de cadastro de um usuário"""
        user = db.query(User).filter(User.id_usuario == user_id).first()
        if user:
            user.status_cadastro = new_status
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def create_base_user(db: Session, user_data: UserBase, categoria: CategoriaEnum, unidade: Unidade) -> User:
        """Cria o usuário base na tabela usuario"""
        user = User(
            id_categoria_usuario=categoria,
            nome=user_data.nome,
            email=user_data.email,
            cpf=user_data.cpf,
            telefone=user_data.telefone,
            status_cadastro=StatusCadastroEnum.PENDENTE,
            id_unidade=unidade.id_unidade
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_aluno(db: Session, user_data: UserAlunoSchema, base_user: User) -> UserAluno:
        """Cria registro específico de aluno"""
        # TODO: Adicionar o campo id_aluno_graduacao e talvez adicionar o campo RA no futuro
        user = UserAluno(
            id_usuario=base_user.id_usuario,
            #id_aluno_graduacao=user_data.ra
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_professor(db: Session, user_data: UserProfessorSchema, base_user: User) -> UserProfessor:
        """Cria registro específico de professor"""
        # TODO: talvez as disciplinas que o professor leciona
        user = UserProfessor(
            id_usuario=base_user.id_usuario,
            id_curso=user_data.curso_id
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_coordenador(db: Session, user_data: UserCoordenacaoSchema, base_user: User) -> UserCoordenador:
        """Cria registro específico de coordenador"""
        user = UserCoordenador(
            id_usuario=base_user.id_usuario,
            id_curso=user_data.curso_id
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_departamento(db: Session, user_data: UserDepartamentoSchema, base_user: User) -> UserDepartamento:
        """Cria registro específico de departamento"""
        user = UserDepartamento(
            id_usuario=base_user.id_usuario,
            id_departamento=user_data.departamento_id
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    # TODO: Aguardar essas duas entidades serem criadas no banco para terminar a funcao
    @staticmethod
    def create_usuario_pro_reitor(db: Session, user_data: UserProReitorSchema, base_user: User):
        """Cria registro específico de pro-reitor"""
        pass
    
    @staticmethod
    def create_usuario_reitor(db: Session, user_data: UserReitorSchema, base_user: User):
        """Cria registro específico de reitor"""
        pass
    
    @staticmethod
    def create_documento_usuario(db: Session, saved_file: SavedFile, usuario_id: int) -> DocumentoUsuario:
        """Cria registro de documento do usuário"""
        document = DocumentoUsuario(
            id_usuario=usuario_id, 
            tipo_documento="COMPROVANTE_VINCULO",
            storage_provider="LOCAL",
            storage_bucket="local-documents",
            storage_key=str(saved_file.base_path / saved_file.filename),
            hash_arquivo="hash_fake_comp_456",
            mime_type=saved_file.mime_type,
            tamanho_arquivo=saved_file.size,
            status_analise=StatusAnaliseEnum.PENDENTE
        )
        
        db.add(document)
        db.flush()
        
        return document