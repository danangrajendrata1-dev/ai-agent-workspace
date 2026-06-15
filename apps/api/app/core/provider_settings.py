from typing import Final


MODEL_PROVIDER_OPENAI: Final[str] = "openai"
MODEL_PROVIDER_ANTHROPIC: Final[str] = "anthropic"
MODEL_PROVIDER_GOOGLE_GEMINI: Final[str] = "google_gemini"
MODEL_PROVIDER_OPENROUTER: Final[str] = "openrouter"
MODEL_PROVIDER_OLLAMA_LOCAL: Final[str] = "ollama_local"
MODEL_PROVIDER_CUSTOM: Final[str] = "custom"

SUPPORTED_MODEL_PROVIDER_IDS: Final[tuple[str, ...]] = (
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENROUTER,
    MODEL_PROVIDER_OLLAMA_LOCAL,
    MODEL_PROVIDER_CUSTOM,
)

CONNECTION_STATUS_NOT_CONNECTED: Final[str] = "not_connected"
CONNECTION_STATUS_METADATA_CONFIGURED: Final[str] = "metadata_configured"
SUPPORTED_CONNECTION_STATUSES: Final[tuple[str, ...]] = (
    CONNECTION_STATUS_NOT_CONNECTED,
    CONNECTION_STATUS_METADATA_CONFIGURED,
)

MAX_PREFERRED_MODEL_LENGTH: Final[int] = 120
SECRET_LIKE_MARKERS: Final[tuple[str, ...]] = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "token",
)


def normalize_optional_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return value

    normalized = value.strip()
    return normalized or None


def looks_secret_like(value: str | None) -> bool:
    if not value:
        return False

    normalized = value.strip().lower()
    if not normalized:
        return False

    if normalized.startswith(("http://", "https://")):
        return True

    if normalized.startswith(("sk-", "rk-", "pk-", "ghp_", "gho_", "github_pat_")):
        return True

    return any(marker in normalized for marker in SECRET_LIKE_MARKERS)


def derive_connection_status(*, preferred_provider: str | None, preferred_model: str | None) -> str:
    if preferred_provider or preferred_model:
        return CONNECTION_STATUS_METADATA_CONFIGURED
    return CONNECTION_STATUS_NOT_CONNECTED
