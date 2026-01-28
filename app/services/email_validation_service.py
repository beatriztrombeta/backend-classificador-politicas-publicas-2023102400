import os
from typing import List


class InvalidEmailError(Exception):
    pass


class InvalidInstitutionalDomainError(Exception):
    pass


class EmailValidationService:
    def __init__(self, allowed_domains: List[str] | None = None):
        if allowed_domains is None:
            domains_env = os.getenv("ALLOWED_EMAIL_DOMAINS", "")
            allowed_domains = [
                domain.strip().lower()
                for domain in domains_env.split(",")
                if domain.strip()
            ]

        self.allowed_domains = allowed_domains

    def validate(self, email: str) -> bool:
        if not email or "@" not in email:
            raise InvalidEmailError("invalid_email_format")

        domain = email.split("@")[-1].lower()

        if domain not in self.allowed_domains:
            raise InvalidInstitutionalDomainError("invalid_institutional_domain")

        return True
