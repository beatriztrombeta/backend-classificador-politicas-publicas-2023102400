def admin_document_review_email(
    admin_name: str,
    user_name: str,
    user_email: str,
    approve_link: str,
    reject_link: str
) -> tuple[str, str]:
    subject = "Cadastro pendente para análise"

    body = f"""
Olá, {admin_name},

Um novo usuário possui cadastro pendente de análise documental.

Dados do usuário:
Nome: {user_name}
E-mail: {user_email}

Ações disponíveis:

Aprovar cadastro:
{approve_link}

Rejeitar cadastro:
{reject_link}

Observações:
- Os links são pessoais e intransferíveis.
- O token expira automaticamente.
- Após a ação, o link se torna inválido.

Atenciosamente,
Sistema de Cadastro Institucional
""".strip()

    return subject, body

def admin_document_review_email(
    admin_name: str,
    user_name: str,
    user_email: str,
    approve_link: str,
    reject_link: str
) -> tuple[str, str]:
    subject = "Cadastro pendente para análise"

    body = f"""
Olá, {admin_name},

Um novo usuário possui cadastro pendente de análise documental.

Dados do usuário:
Nome: {user_name}
E-mail: {user_email}

Ações disponíveis:

Aprovar cadastro:
{approve_link}

Rejeitar cadastro:
{reject_link}

Observações:
- Os links são pessoais e intransferíveis.
- O token expira automaticamente.
- Após a ação, o link se torna inválido.

Atenciosamente,
Sistema de Cadastro Institucional
""".strip()

    return subject, body


def user_approval_email(user_name: str, login_url: str) -> tuple[str, str]:
    """Template de email para notificar usuário sobre aprovação do cadastro"""
    subject = "Cadastro aprovado - Bem-vindo ao sistema"

    body = f"""
Olá, {user_name},

Sua documentação foi analisada e aprovada com sucesso!

Agora você já pode acessar o sistema utilizando suas credenciais institucionais.

Acesse o sistema:
{login_url}

Observações:
- Utilize seu e-mail institucional para fazer login.
- Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Sistema de Cadastro Institucional
""".strip()

    return subject, body


def user_rejection_email(user_name: str, contact_email: str) -> tuple[str, str]:
    """Template de email para notificar usuário sobre rejeição do cadastro"""
    subject = "Cadastro não aprovado - Ação necessária"

    body = f"""
Olá, {user_name},

Infelizmente, sua documentação não foi aprovada após análise.

Motivos possíveis:
- Documentação incompleta ou ilegível
- Informações inconsistentes
- Documentação não atende aos requisitos institucionais

Próximos passos:
Para mais informações sobre os motivos da recusa e orientações sobre como proceder, 
entre em contato através do e-mail: {contact_email}

Atenciosamente,
Sistema de Cadastro Institucional
""".strip()

    return subject, body