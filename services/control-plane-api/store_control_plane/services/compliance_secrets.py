from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status


class ComplianceSecretsService:
    def __init__(self, *, secret_key: str | None):
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Compliance secret key is not configured",
            )
        self._fernet = Fernet(secret_key.encode("utf-8"))

    def encrypt_password(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt_password(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stored compliance credentials are unreadable",
            ) from error
