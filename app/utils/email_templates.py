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