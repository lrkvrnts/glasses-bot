"""Fernet-based encryption for API keys."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from bot.config.settings import get_settings
from bot.core.exceptions import AppError


class EncryptionError(AppError):
    user_message = "Ошибка шифрования. Проверь ENCRYPTION_KEY."


class EncryptionService:
    """Шифрует/расшифровывает строки через Fernet."""

    def __init__(self, key: str | bytes | None = None) -> None:
        if key is None:
            key = get_settings().encryption_key
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise EncryptionError(f"Invalid ENCRYPTION_KEY: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        """Шифрует строку, возвращает base64-токен."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Расшифровывает токен обратно в строку."""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            raise EncryptionError("Failed to decrypt token") from e
