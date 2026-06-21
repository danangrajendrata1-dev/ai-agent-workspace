from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent_avatar_asset import AgentAvatarAsset
from app.repositories import agent_avatar_repository, agent_repository
from app.schemas.agent import AgentAvatarStoredType, AgentAvatarUploadResponse


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
GIF87_MAGIC = b"GIF87a"
GIF89_MAGIC = b"GIF89a"
WEBP_MAGIC_PREFIX = b"RIFF"
WEBP_MAGIC_MARKER = b"WEBP"
SVG_LIKE_MARKERS = (b"<svg", b"<?xml", b"<!doctype html", b"<html", b"<script")
DEFAULT_ALLOWED_MIME_TYPES = ("image/png", "image/jpeg", "image/webp", "image/gif")


def build_avatar_content_url(agent_id: uuid.UUID) -> str:
    return f"/agents/{agent_id}/avatar/content"


def normalize_agent_avatar_fields(
    avatar_type: str | None,
    avatar_value: str | None,
) -> tuple[AgentAvatarStoredType | None, str | None]:
    if avatar_type is None and avatar_value is None:
        return None, None

    if avatar_type is None or avatar_value is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="avatar_type and avatar_value must be provided together.",
        )

    normalized_type = str(avatar_type).strip()
    normalized_value = str(avatar_value).strip()

    if not normalized_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Avatar value cannot be empty.",
        )

    if normalized_type == "emoji":
        if len(normalized_value) > 16:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Emoji avatar must be 16 characters or fewer.",
            )
        return "emoji", normalized_value

    if normalized_type not in {"image_url", "animation_url"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported avatar type.",
        )

    return normalized_type, _normalize_http_url(normalized_value)


def _normalize_http_url(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Avatar URL must be 500 characters or fewer.",
        )
    if trimmed.startswith("//") or trimmed.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Avatar URL must be absolute http or https.",
        )

    parsed = urlparse(trimmed)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Avatar URL must use http or https.",
        )

    return trimmed


def sanitize_filename(filename: str | None, *, ext: str) -> str:
    base_name = Path(filename or "").name.replace("\x00", "").strip()
    base_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._-")
    if not base_name:
        base_name = f"avatar.{ext}"
    if len(base_name) > 120:
        base_name = base_name[:120]
    if "." not in base_name:
        base_name = f"{base_name}.{ext}"
    return base_name


def _resolve_workspace_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_local_dir() -> Path:
    settings = get_settings()
    raw_dir = Path(settings.agent_avatar_local_dir)
    if raw_dir.is_absolute():
        return raw_dir
    return _resolve_workspace_root() / raw_dir


def _normalize_storage_prefix(prefix: str) -> str:
    return prefix.strip().strip("/").replace("\\", "/")


def _build_storage_key(
    *,
    user_id: uuid.UUID,
    agent_id: uuid.UUID,
    asset_id: uuid.UUID,
    ext: str,
    storage_token: str,
) -> str:
    settings = get_settings()
    prefix = _normalize_storage_prefix(settings.agent_avatar_gcs_prefix or "agent-avatars")
    return f"{prefix}/{user_id}/{agent_id}/{asset_id}/{storage_token}.{ext}"


def _sniff_avatar_file(
    data: bytes,
    *,
    original_filename: str | None,
    declared_content_type: str | None,
    allowed_mime_types: set[str],
) -> tuple[str, str, bool, str]:
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file cannot be empty.",
        )

    filename = (original_filename or "").strip().lower()
    declared_type = (declared_content_type or "").strip().lower()
    prefix = data[:512].lstrip().lower()

    if filename.endswith(".svg") or declared_type.startswith("image/svg+xml") or any(marker in prefix for marker in SVG_LIKE_MARKERS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SVG and HTML-like avatars are not allowed.",
        )

    if data.startswith(PNG_MAGIC):
        detected_mime = "image/png"
        ext = "png"
        animation = False
    elif data.startswith(JPEG_MAGIC):
        detected_mime = "image/jpeg"
        ext = "jpg"
        animation = False
    elif data.startswith(GIF87_MAGIC) or data.startswith(GIF89_MAGIC):
        detected_mime = "image/gif"
        ext = "gif"
        animation = True
    elif len(data) >= 12 and data.startswith(WEBP_MAGIC_PREFIX) and data[8:12] == WEBP_MAGIC_MARKER:
        detected_mime = "image/webp"
        ext = "webp"
        animation = False
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported avatar file type.",
        )

    if detected_mime not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file type is not allowed.",
        )

    safe_filename = sanitize_filename(original_filename, ext=ext)
    return detected_mime, ext, animation, safe_filename


async def read_upload_file_bytes(upload_file: UploadFile, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0

    try:
        while True:
            chunk = await upload_file.read(64 * 1024)
            if not chunk:
                break

            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Avatar file exceeds the {max_bytes} byte limit.",
                )

            chunks.append(chunk)
    finally:
        await upload_file.close()

    return b"".join(chunks)


def _local_object_path(storage_key: str) -> Path:
    return _resolve_local_dir() / storage_key


def _store_local_object(storage_key: str, data: bytes) -> None:
    path = _local_object_path(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _read_local_object(storage_key: str) -> bytes:
    path = _local_object_path(storage_key)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar content not found.",
        )
    return path.read_bytes()


def _delete_local_object(storage_key: str) -> None:
    path = _local_object_path(storage_key)
    if path.exists():
        path.unlink()


def _store_gcs_object(storage_key: str, data: bytes, *, content_type: str) -> None:
    settings = get_settings()
    try:
        from google.cloud import storage as gcs_storage
    except ImportError as exc:  # pragma: no cover - only used in production gcs setup
        raise RuntimeError("google-cloud-storage package is required when AGENT_AVATAR_STORAGE_BACKEND=gcs.") from exc

    client = gcs_storage.Client()
    bucket = client.bucket(settings.agent_avatar_gcs_bucket)
    blob = bucket.blob(storage_key)
    blob.upload_from_string(data, content_type=content_type)


def _read_gcs_object(storage_key: str) -> bytes:
    settings = get_settings()
    try:
        from google.cloud import storage as gcs_storage
    except ImportError as exc:  # pragma: no cover - only used in production gcs setup
        raise RuntimeError("google-cloud-storage package is required when AGENT_AVATAR_STORAGE_BACKEND=gcs.") from exc

    client = gcs_storage.Client()
    bucket = client.bucket(settings.agent_avatar_gcs_bucket)
    blob = bucket.blob(storage_key)
    if not blob.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar content not found.",
        )
    return blob.download_as_bytes()


def _delete_gcs_object(storage_key: str) -> None:
    settings = get_settings()
    try:
        from google.cloud import storage as gcs_storage
    except ImportError as exc:  # pragma: no cover - only used in production gcs setup
        raise RuntimeError("google-cloud-storage package is required when AGENT_AVATAR_STORAGE_BACKEND=gcs.") from exc

    client = gcs_storage.Client()
    bucket = client.bucket(settings.agent_avatar_gcs_bucket)
    blob = bucket.blob(storage_key)
    if blob.exists():
        blob.delete()


def _store_object(storage_key: str, data: bytes, *, content_type: str) -> None:
    settings = get_settings()
    if settings.agent_avatar_storage_backend == "gcs":
        _store_gcs_object(storage_key, data, content_type=content_type)
    else:
        _store_local_object(storage_key, data)


def _read_object(storage_key: str) -> bytes:
    settings = get_settings()
    if settings.agent_avatar_storage_backend == "gcs":
        return _read_gcs_object(storage_key)
    return _read_local_object(storage_key)


def _delete_object(storage_key: str) -> None:
    settings = get_settings()
    if settings.agent_avatar_storage_backend == "gcs":
        _delete_gcs_object(storage_key)
    else:
        _delete_local_object(storage_key)


def _resolve_avatar_type_for_upload(*, detected_mime: str, requested_kind: str | None) -> AgentAvatarStoredType:
    normalized_kind = (requested_kind or "").strip() or None
    if detected_mime == "image/gif":
        return "uploaded_animation"

    if detected_mime == "image/webp":
        if normalized_kind == "uploaded_animation":
            return "uploaded_animation"
        return "uploaded_image"

    if normalized_kind == "uploaded_animation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded_animation is only allowed for GIF or WebP avatars.",
        )

    return "uploaded_image"


def _build_upload_response(agent, asset: AgentAvatarAsset) -> AgentAvatarUploadResponse:
    return AgentAvatarUploadResponse.model_validate(
        {
            "id": asset.id,
            "agent_id": agent.id,
            "avatar_type": agent.avatar_type,
            "avatar_value": agent.avatar_value,
            "content_type": asset.content_type,
            "size_bytes": asset.size_bytes,
            "safe_filename": asset.safe_filename,
            "sha256": asset.sha256,
            "avatar_content_url": build_avatar_content_url(agent.id),
        }
    )


def upload_agent_avatar(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: bytes,
    original_filename: str | None,
    declared_content_type: str | None,
    avatar_kind: str | None,
) -> AgentAvatarUploadResponse:
    settings = get_settings()
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    detected_mime, extension, _, safe_filename = _sniff_avatar_file(
        data,
        original_filename=original_filename,
        declared_content_type=declared_content_type,
        allowed_mime_types=set(settings.agent_avatar_allowed_mime_types or DEFAULT_ALLOWED_MIME_TYPES),
    )
    resolved_avatar_type = _resolve_avatar_type_for_upload(
        detected_mime=detected_mime,
        requested_kind=avatar_kind,
    )

    asset = agent_avatar_repository.get_by_agent_id(db, owner_id=owner_id, agent_id=agent.id)
    previous_storage_key = asset.storage_key if asset else None
    if asset is None:
        asset = AgentAvatarAsset(
            id=uuid.uuid4(),
            user_id=owner_id,
            agent_id=agent.id,
            storage_backend=settings.agent_avatar_storage_backend,
            storage_key="",
            original_filename=original_filename,
            safe_filename=safe_filename,
            content_type=detected_mime,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        db.add(asset)

    storage_key = _build_storage_key(
        user_id=owner_id,
        agent_id=agent.id,
        asset_id=asset.id,
        ext=extension,
        storage_token=uuid.uuid4().hex,
    )

    try:
        _store_object(storage_key, data, content_type=detected_mime)
        asset.storage_backend = settings.agent_avatar_storage_backend
        asset.storage_key = storage_key
        asset.original_filename = original_filename
        asset.safe_filename = safe_filename
        asset.content_type = detected_mime
        asset.size_bytes = len(data)
        asset.sha256 = hashlib.sha256(data).hexdigest()

        agent.avatar_type = resolved_avatar_type
        agent.avatar_value = str(asset.id)
        db.add(agent)
        db.add(asset)
        db.commit()
        db.refresh(agent)
        db.refresh(asset)
    except Exception:
        db.rollback()
        _delete_object(storage_key)
        raise

    if previous_storage_key and previous_storage_key != storage_key:
        try:
            _delete_object(previous_storage_key)
        except Exception:
            pass

    return _build_upload_response(agent, asset)


def get_agent_avatar_content(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[bytes, str]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    if agent.avatar_type not in {"uploaded_image", "uploaded_animation"} or not agent.avatar_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent avatar content not found.",
        )

    asset = agent_avatar_repository.get_by_agent_id(db, owner_id=owner_id, agent_id=agent.id)
    if asset is None or str(asset.id) != str(agent.avatar_value):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent avatar content not found.",
        )

    content = _read_object(asset.storage_key)
    return content, asset.content_type


def delete_agent_avatar(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID):
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    asset = agent_avatar_repository.get_by_agent_id(db, owner_id=owner_id, agent_id=agent.id)
    if asset is not None:
        try:
            _delete_object(asset.storage_key)
        except Exception:
            pass
        agent_avatar_repository.delete_by_agent_id(db, owner_id=owner_id, agent_id=agent.id)

    agent.avatar_type = None
    agent.avatar_value = None
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent
