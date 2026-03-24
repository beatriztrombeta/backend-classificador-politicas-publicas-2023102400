from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List
from app.models.user_model import (
    User, Unidade, UserAluno, UserProfessor, 
    UserCoordenador, UserDepartamento, DocumentoUsuario,
    StatusCadastroEnum, StatusAnaliseEnum, Disciplina, Curso,
    Departamento, UserCategory, UserProrei, UserReitor, TipoProreitoria, Campus,
    Aluno, UserAdmin
)
from app.schemas.user_schema import (
    UserBase, UserAluno as UserAlunoSchema, 
    UserProfessor as UserProfessorSchema,
    UserCoordenacao as UserCoordenacaoSchema,
    UserDepartamento as UserDepartamentoSchema,
    UserProReitor as UserProReitorSchema,
    UserReitor as UserReitorSchema,
    UserAdmin as UserAdminSchema,
    CategoriaEnum, SavedFile,
    DisciplinaNotFoundError,
    DuplicatedDisciplinaError,
    CursoNotFoundError,
    DepartamentoNotFoundError,
    CategoriaNotFoundError,
    CampusNotFoundError,
    TipoProreitoriaNotFoundError,
    UnidadeNotFoundError,
    AlunoNotFoundError,
    EmptyDisciplinaListError
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
        return db.query(User).filter(User.id_categoria_usuario == 1).all()
    
    @staticmethod
    def update_status(db: Session, user_id: int, new_status: str):
        """Atualiza o status de cadastro de um usuário"""
        user = db.query(User).filter(User.id_usuario == user_id).first()

        if not user:
            raise ValueError("Usuário não encontrado")

        user.status_cadastro = new_status
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_base_user(db: Session, user_data: UserBase, categoria: CategoriaEnum) -> User:
        """Cria o usuário base na tabela usuario"""
        print(categoria.value)
        existing_categoria = (
            db.query(UserCategory)
            .filter(func.trim(UserCategory.nome_categoria) == categoria.value)
            .one_or_none()
        )

        if not existing_categoria:
            raise CategoriaNotFoundError()
        
        user = User(
            id_categoria_usuario=existing_categoria.id_categoria_usuario,
            nome=user_data.nome,
            email=user_data.email,
            cpf=user_data.cpf,
            telefone=user_data.telefone,
            status_cadastro=StatusCadastroEnum.PENDENTE
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_aluno(db: Session, user_data: UserAlunoSchema, base_user: User) -> UserAluno:
        """Cria registro específico de aluno"""
        unidade = (
            db.query(Unidade)
            .filter(Unidade.id_unidade == user_data.unidade_id)
            .one_or_none()
        )
        if not unidade:
            raise UnidadeNotFoundError()
        
        aluno = (
            db.query(Aluno)
            .filter(Aluno.id_aluno_graduacao == int(user_data.ra))
            .one_or_none()
        )
        if not aluno:
            raise AlunoNotFoundError()

        user = UserAluno(
            id_usuario=base_user.id_usuario,
            id_unidade=user_data.unidade_id,
            id_aluno_graduacao=int(user_data.ra)
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_professor(db: Session, user_data: UserProfessorSchema, base_user: User) -> UserProfessor:
        """Cria registros de professor"""

        if not user_data.disciplinas:
            raise EmptyDisciplinaListError()

        existing_disciplinas = (
            db.query(Disciplina)
            .filter(Disciplina.id_disciplina.in_(user_data.disciplinas))
            .all()
        )

        existing_ids = {d.id_disciplina for d in existing_disciplinas}
        invalid_ids = set(user_data.disciplinas) - existing_ids
        if invalid_ids:
            raise DisciplinaNotFoundError()

        if len(set(user_data.disciplinas)) != len(user_data.disciplinas):
            raise DuplicatedDisciplinaError()

        unidade = (
            db.query(Unidade)
            .filter(Unidade.id_unidade == user_data.unidade_id)
            .one_or_none()
        )
        if not unidade:
            raise UnidadeNotFoundError()

        users = [
            UserProfessor(
                id_usuario=base_user.id_usuario,
                id_disciplina=disciplina,
                id_unidade=user_data.unidade_id
            )
            for disciplina in user_data.disciplinas
        ]

        db.add_all(users)
        db.flush()

        return users[0]
    
    @staticmethod
    def create_usuario_coordenador(db: Session, user_data: UserCoordenacaoSchema, base_user: User) -> UserCoordenador:
        """Cria registro específico de coordenador"""
        curso = (
            db.query(Curso)
            .filter(Curso.id_curso == user_data.curso_id)
            .one_or_none()
        )
        
        if not curso:
            raise CursoNotFoundError()

        unidade = (
            db.query(Unidade)
            .filter(Unidade.id_unidade == user_data.unidade_id)
            .one_or_none()
        )
        if not unidade:
            raise UnidadeNotFoundError()

        user = UserCoordenador(
            id_usuario=base_user.id_usuario,
            id_curso=user_data.curso_id,
            id_unidade=user_data.unidade_id
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_departamento(db: Session, user_data: UserDepartamentoSchema, base_user: User) -> UserDepartamento:
        """Cria registro específico de departamento"""
        depto = (
            db.query(Departamento)
            .filter(Departamento.id_departamento == user_data.departamento_id)
            .one_or_none()
        )
        
        if not depto:
            raise DepartamentoNotFoundError()
        
        unidade = (
            db.query(Unidade)
            .filter(Unidade.id_unidade == user_data.unidade_id)
            .one_or_none()
        )
        if not unidade:
            raise UnidadeNotFoundError()

        user = UserDepartamento(
            id_usuario=base_user.id_usuario,
            id_departamento=user_data.departamento_id,
            id_unidade=user_data.unidade_id
        )
        
        db.add(user)
        db.flush()
        
        return user
    
    @staticmethod
    def create_usuario_pro_reitor(db: Session, user_data: UserProReitorSchema, base_user: User):
        """Cria registro específico de pro-reitor"""
        campus = (
            db.query(Campus)
            .filter(Campus.id_campus == user_data.campus_id)
            .one_or_none()
        )
        
        if not campus:
            raise CampusNotFoundError()
        
        tipo = (
            db.query(TipoProreitoria)
            .filter(TipoProreitoria.id_tipo_proreitoria == user_data.proreitoria_id)
            .one_or_none()
        )

        if not tipo:
            raise TipoProreitoriaNotFoundError()

        user = UserProrei(
                id_usuario=base_user.id_usuario,
                id_campus=user_data.campus_id,
                id_proreitoria=user_data.proreitoria_id
            )
        
        db.add(user)
        db.flush()

        return user
    
    @staticmethod
    def create_usuario_reitor(db: Session, user_data: UserReitorSchema, base_user: User):
        """Cria registro específico de reitor"""
        campus = (
            db.query(Campus)
            .filter(Campus.id_campus == user_data.campus_id)
            .one_or_none()
        )
        
        if not campus:
            raise CampusNotFoundError()

        user = UserReitor(
                id_usuario=base_user.id_usuario,
                id_campus=user_data.campus_id
            )
        
        db.add(user)
        db.flush()

        return user
    
    @staticmethod
    def create_documento_usuario(db: Session, saved_file: SavedFile, usuario_id: int) -> DocumentoUsuario:
        document = DocumentoUsuario(
            id_usuario=usuario_id,
            tipo_documento="COMPROVANTE_VINCULO",
            storage_provider="LOCAL",
            storage_bucket="local-documents",
            storage_key=saved_file.relative_path,
            hash_arquivo="hash_fake_comp_456",
            mime_type=saved_file.mime_type,
            tamanho_arquivo=saved_file.size,
            status_analise=StatusAnaliseEnum.PENDENTE
        )

        db.add(document)
        db.flush()

        return document
    
    @staticmethod
    def create_usuario_admin(db: Session, user_data: UserAdminSchema, base_user: User) -> User:
        """Cria registro específico de admin"""
        campus = (
            db.query(Campus)
            .filter(Campus.id_campus == user_data.campus_id)
            .one_or_none()
        )
        if not campus:
            raise CampusNotFoundError()

        admin = UserAdmin(
            id_usuario=base_user.id_usuario,
            id_campus=user_data.campus_id
        )

        db.add(admin)
        db.flush()

        return base_user

    @staticmethod
    def list_pending_users(db: Session) -> List[User]:
        """Lista todos os usuários que estão com o cadastro pendente"""
        return db.query(User).filter(User.status_cadastro == StatusCadastroEnum.PENDENTE).all()
    
    @staticmethod
    def list_documents(db: Session) -> List[DocumentoUsuario]:
        """Lista todos os documentos cadastrados"""
        return db.query(DocumentoUsuario).all()
    
    @staticmethod
    def _list_users_admin_base(
        db: Session,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
        order_asc: bool = False,
    ):
        order_clause = "ASC" if order_asc else "DESC"

        params = {
            "limit": limit,
            "offset": offset,
            "status": status,
        }

        query = text(f"""
            WITH categoria AS (
                SELECT
                    cu.id_categoria_usuario,
                    TRIM(cu.nome_categoria) AS nome_categoria
                FROM categoria_usuario cu
            ),
            campus_direto AS (
                SELECT ua.id_usuario, ua.id_campus
                FROM usuario_admin ua
                UNION ALL
                SELECT ur.id_usuario, ur.id_campus
                FROM usuario_reitor ur
                UNION ALL
                SELECT up.id_usuario, up.id_campus
                FROM usuario_prorei up
            ),
            unidade_por_usuario AS (
                SELECT x.id_usuario, MAX(x.id_unidade) AS id_unidade
                FROM (
                    SELECT ua.id_usuario, ua.id_unidade FROM usuario_aluno ua
                    UNION ALL
                    SELECT up.id_usuario, up.id_unidade FROM usuario_professor up
                    UNION ALL
                    SELECT uc.id_usuario, uc.id_unidade FROM usuario_coordenador uc
                    UNION ALL
                    SELECT ud.id_usuario, ud.id_unidade FROM usuario_departamento ud
                ) x
                GROUP BY x.id_usuario
            ),
            documentos_por_usuario AS (
                SELECT
                    du.id_usuario,
                    json_agg(
                        json_build_object(
                            'id_documento', du.id_documento,
                            'tipo_documento', du.tipo_documento,
                            'nome_arquivo', split_part(du.storage_key, '/', array_length(string_to_array(du.storage_key, '/'), 1)),
                            'mime_type', du.mime_type,
                            'tamanho_arquivo', du.tamanho_arquivo,
                            'data_envio', du.data_envio,
                            'status_analise', du.status_analise,
                            'download_url', CONCAT('/users/documents/download/', du.id_documento)
                        )
                        ORDER BY du.data_envio DESC
                    ) AS documentos
                FROM documento_usuario du
                GROUP BY du.id_usuario
            )
            SELECT
                u.id_usuario AS id,
                u.nome,
                c.nome_categoria AS categoria,
                COALESCE(camp_direto.nome_campus, camp_unidade.nome_campus) AS campus,
                u.data_cadastro,
                u.data_atualizacao,
                COALESCE(dpu.documentos, '[]'::json) AS documentos,
                u.status_cadastro AS status
            FROM usuario u
            INNER JOIN categoria c
                ON c.id_categoria_usuario = u.id_categoria_usuario
            LEFT JOIN campus_direto cd
                ON cd.id_usuario = u.id_usuario
            LEFT JOIN campus camp_direto
                ON camp_direto.id_campus = cd.id_campus
            LEFT JOIN unidade_por_usuario uu
                ON uu.id_usuario = u.id_usuario
            LEFT JOIN unidade un
                ON un.id_unidade = uu.id_unidade
            LEFT JOIN campus camp_unidade
                ON camp_unidade.id_campus = un.id_campus
            LEFT JOIN documentos_por_usuario dpu
                ON dpu.id_usuario = u.id_usuario
            WHERE (:status IS NULL OR u.status_cadastro = CAST(:status AS status_cadastro_enum))
            ORDER BY u.data_cadastro {order_clause}
            LIMIT :limit OFFSET :offset
        """)

        rows = db.execute(query, params).mappings().all()
        return [dict(row) for row in rows]
    
    @staticmethod
    def list_pending_users_admin(db: Session, limit: int):
        return UserRepository._list_users_admin_base(
            db=db,
            status="PENDENTE",
            limit=limit,
            offset=0,
            order_asc=True,
        )

    @staticmethod
    def list_users_admin(db: Session, status: str | None, limit: int, offset: int):
        return UserRepository._list_users_admin_base(
            db=db,
            status=status,
            limit=limit,
            offset=offset,
            order_asc=False,
        )