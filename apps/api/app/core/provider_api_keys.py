from typing import Final

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.provider_settings import (
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_CUSTOM,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_OPENROUTER,
)


SUPPORTED_API_KEY_PROVIDER_IDS: Final[tuple[str, ...]] = (
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENROUTER,
    MODEL_PROVIDER_CUSTOM,
)

API_KEY_CONNECTION_STATUS_CONNECTED: Final[str] = "connected"
API_KEY_CONNECTION_STATUS_NOT_CONNECTED: Final[str] = "not_connected"
API_KEY_MASK_PREFIX: Final[str] = "********"


def normalize_provider_id(provider_id: str | None) -> str | None:
    if not isinstance(provider_id, str):
        return provider_id
    normalized = provider_id.strip().lower()
    return normalized or None


def validate_api_key_provider(provider_id: str | None) -> str:
    normalized = normalize_provider_id(provider_id)
    if normalized is None or normalized not in SUPPORTED_API_KEY_PROVIDER_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider for API key storage.",
        )
    return normalized


def mask_api_key(last4: str | None) -> str | None:
    if not last4:
        return None
    return f"{API_KEY_MASK_PREFIX}{last4}"


def normalize_api_key(api_key: str | None) -> str | None:
    if not isinstance(api_key, str):
        return None

    normalized = api_key.strip()
    return normalized or None


def get_api_key_last4(api_key: str) -> str:
    return api_key[-4:] if len(api_key) >= 4 else api_key


def get_api_key_fernet() -> Fernet:
    encryption_key = get_settings().provider_api_key_encryption_key
    if not encryption_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provider API key encryption is not configured.",
        )

    try:
        return Fernet(encryption_key.encode())
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provider API key encryption is not configured.",
        )


def encrypt_api_key(api_key: str) -> str:
    fernet = get_api_key_fernet()
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    fernet = get_api_key_fernet()
    try:
        return fernet.decrypt(encrypted_api_key.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provider API key encryption is not configured.",
        )
