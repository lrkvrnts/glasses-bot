"""Tests for EncryptionService."""

import pytest
from cryptography.fernet import Fernet

from bot.services.encryption import EncryptionError, EncryptionService


@pytest.fixture
def valid_key() -> str:
    return Fernet.generate_key().decode()


def test_encrypt_decrypt_roundtrip(valid_key: str):
    """Шифр + дешифр = исходный текст."""
    svc = EncryptionService(key=valid_key)
    plaintext = "my-secret-api-key-12345"

    encrypted = svc.encrypt(plaintext)
    decrypted = svc.decrypt(encrypted)

    assert decrypted == plaintext


def test_encrypt_produces_different_ciphertext_each_time(valid_key: str):
    """Fernet использует случайный IV — ciphertext каждый раз разный."""
    svc = EncryptionService(key=valid_key)
    plain = "same-input"

    a = svc.encrypt(plain)
    b = svc.encrypt(plain)

    assert a != b


def test_decrypt_invalid_token_raises(valid_key: str):
    """Невалидный токен → EncryptionError."""
    svc = EncryptionService(key=valid_key)

    with pytest.raises(EncryptionError):
        svc.decrypt("not-a-valid-token")


def test_invalid_key_raises_on_init():
    """Невалидный ключ при создании сервиса → EncryptionError."""
    with pytest.raises(EncryptionError):
        EncryptionService(key="not-a-valid-fernet-key")


def test_unicode_roundtrip(valid_key: str):
    """Unicode в открытом тексте корректно шифруется."""
    svc = EncryptionService(key=valid_key)
    plain = "Привет, мир! 👋"

    assert svc.decrypt(svc.encrypt(plain)) == plain
