import uuid
from types import SimpleNamespace

import pytest

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.repositories import user_repository


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16
GIF_BYTES = b"GIF89a" + b"\x00" * 16
WEBP_BYTES = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 16
HTML_BYTES = b"<!doctype html><html><body>nope</body></html>"
SVG_BYTES = b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'></svg>"


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


@pytest.fixture(autouse=True)
def avatar_storage_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_AVATAR_STORAGE_BACKEND", "local")
    monkeypatch.setenv("AGENT_AVATAR_LOCAL_DIR", str(tmp_path / "agent-avatars"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def build_user(db, *, email_prefix: str, plan: str = "pro"):
    user = user_repository.create_user(
        db,
        email=f"{email_prefix}-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hash",
        display_name="Avatar User",
        role="user",
        subscription_plan=plan,
    )
    db.commit()
    db.refresh(user)
    return SimpleNamespace(id=user.id, role=user.role, subscription_plan=user.subscription_plan)


def build_agent_payload(name: str = "Avatar Agent", **overrides):
    unique_name = f"{name}-{uuid.uuid4().hex[:8]}"
    payload = {
        "name": unique_name[:120],
        "role_description": "Handles avatar work.",
        "instruction_text": "Use safe avatar rules.",
        "status": "active",
        "max_steps": 10,
        "max_runtime_seconds": 300,
        "requires_approval_by_default": False,
    }
    payload.update(overrides)
    return payload


def create_agent(client, user_id: uuid.UUID, **overrides):
    response = client.post("/agents", headers=auth_headers(user_id), json=build_agent_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def upload_avatar(client, user_id: uuid.UUID, agent_id: str, *, filename: str, content: bytes, content_type: str, avatar_kind: str | None = None):
    data = {}
    if avatar_kind is not None:
        data["avatar_kind"] = avatar_kind

    response = client.post(
        f"/agents/{agent_id}/avatar",
        headers=auth_headers(user_id),
        data=data,
        files={"file": (filename, content, content_type)},
    )
    return response


def test_create_agent_without_avatar_returns_safe_fields(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-create-none")

    payload = create_agent(client, user.id, name="Avatar Free Agent")
    assert payload["avatar_type"] is None
    assert payload["avatar_value"] is None
    assert payload["avatar_content_url"] is None


def test_create_agent_with_emoji_avatar_returns_safe_fields(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-create-emoji")

    payload = create_agent(
        client,
        user.id,
        name="Emoji Agent",
        avatar_type="emoji",
        avatar_value="🤖",
    )
    assert payload["avatar_type"] == "emoji"
    assert payload["avatar_value"] == "🤖"
    assert payload["avatar_content_url"] is None


@pytest.mark.parametrize("emoji_value", ["", "   ", "🤖" * 17])
def test_create_agent_rejects_invalid_emoji_avatar(client, emoji_value):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-create-emoji-reject")

    response = client.post(
        "/agents",
        headers=auth_headers(user.id),
        json=build_agent_payload(
            name="Emoji Reject Agent",
            avatar_type="emoji",
            avatar_value=emoji_value,
        ),
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "avatar_type,avatar_value",
    [
        ("image_url", "http://example.com/avatar.png"),
        ("animation_url", "https://example.com/avatar.gif"),
    ],
)
def test_create_agent_accepts_safe_avatar_urls(client, avatar_type, avatar_value):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-create-url")

    payload = create_agent(
        client,
        user.id,
        name=f"{avatar_type} Agent",
        avatar_type=avatar_type,
        avatar_value=avatar_value,
    )
    assert payload["avatar_type"] == avatar_type
    assert payload["avatar_value"] == avatar_value


@pytest.mark.parametrize(
    "avatar_type,avatar_value",
    [
        ("image_url", "javascript:alert(1)"),
        ("image_url", "data:text/plain;base64,abc"),
        ("image_url", "file:///tmp/avatar.png"),
        ("image_url", "blob:https://example.com/avatar"),
        ("image_url", "chrome://settings"),
        ("image_url", "ftp://example.com/avatar.png"),
        ("image_url", "mailto:test@example.com"),
        ("image_url", "/avatar.png"),
        ("image_url", "//example.com/avatar.png"),
    ],
)
def test_create_agent_rejects_unsafe_avatar_urls(client, avatar_type, avatar_value):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-create-url-reject")

    response = client.post(
        "/agents",
        headers=auth_headers(user.id),
        json=build_agent_payload(
            name="URL Reject Agent",
            avatar_type=avatar_type,
            avatar_value=avatar_value,
        ),
    )
    assert response.status_code == 422


def test_upload_png_avatar_and_read_content(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-png")
    agent = create_agent(client, user.id, name="PNG Avatar Agent")

    upload_response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename="avatar.png",
        content=PNG_BYTES,
        content_type="image/png",
    )
    assert upload_response.status_code == 201, upload_response.text
    upload_payload = upload_response.json()
    assert upload_payload["avatar_type"] == "uploaded_image"
    assert upload_payload["avatar_value"]
    assert upload_payload["avatar_content_url"] == f"/agents/{agent['id']}/avatar/content"

    content_response = client.get(
        f"/agents/{agent['id']}/avatar/content",
        headers=auth_headers(user.id),
    )
    assert content_response.status_code == 200
    assert content_response.headers["content-type"].startswith("image/png")
    assert content_response.headers["x-content-type-options"] == "nosniff"
    assert content_response.headers["cache-control"] == "private, max-age=3600"
    assert content_response.content == PNG_BYTES

    detail_response = client.get(f"/agents/{agent['id']}", headers=auth_headers(user.id))
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["avatar_type"] == "uploaded_image"
    assert detail_payload["avatar_value"] == upload_payload["avatar_value"]
    assert detail_payload["avatar_content_url"] == f"/agents/{agent['id']}/avatar/content"


def test_upload_jpeg_avatar(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-jpeg")
    agent = create_agent(client, user.id, name="JPEG Avatar Agent")

    response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename="avatar.jpg",
        content=JPEG_BYTES,
        content_type="image/jpeg",
    )
    assert response.status_code == 201
    assert response.json()["avatar_type"] == "uploaded_image"


def test_upload_gif_avatar_defaults_to_animation(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-gif")
    agent = create_agent(client, user.id, name="GIF Avatar Agent")

    response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename="avatar.gif",
        content=GIF_BYTES,
        content_type="image/gif",
    )
    assert response.status_code == 201
    assert response.json()["avatar_type"] == "uploaded_animation"


def test_upload_webp_avatar_can_be_animation_when_requested(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-webp")
    agent = create_agent(client, user.id, name="WebP Avatar Agent")

    response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename="avatar.webp",
        content=WEBP_BYTES,
        content_type="image/webp",
        avatar_kind="uploaded_animation",
    )
    assert response.status_code == 201
    assert response.json()["avatar_type"] == "uploaded_animation"


@pytest.mark.parametrize(
    "filename,content_type,content",
    [
        ("avatar.svg", "image/svg+xml", SVG_BYTES),
        ("avatar.png", "text/html", HTML_BYTES),
        ("avatar.png", "image/png", b"not an image"),
    ],
)
def test_upload_rejects_unsafe_or_invalid_content(client, filename, content_type, content):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-reject")
    agent = create_agent(client, user.id, name="Reject Avatar Agent")

    response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename=filename,
        content=content,
        content_type=content_type,
    )
    assert response.status_code in {400, 415, 413}


def test_upload_rejects_oversized_file(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-upload-large")
    agent = create_agent(client, user.id, name="Large Avatar Agent")

    max_bytes = get_settings().agent_avatar_max_bytes
    response = upload_avatar(
        client,
        user.id,
        agent["id"],
        filename="avatar.png",
        content=PNG_BYTES + b"0" * max_bytes,
        content_type="image/png",
    )
    assert response.status_code == 413


def test_non_owner_cannot_upload_to_another_users_agent(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="avatar-owner")
        other = build_user(db, email_prefix="avatar-other")
    agent = create_agent(client, owner.id, name="Owner Avatar Agent")

    response = upload_avatar(
        client,
        other.id,
        agent["id"],
        filename="avatar.png",
        content=PNG_BYTES,
        content_type="image/png",
    )
    assert response.status_code == 404


def test_non_owner_cannot_read_avatar_content(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="avatar-content-owner")
        other = build_user(db, email_prefix="avatar-content-other")
    agent = create_agent(client, owner.id, name="Content Avatar Agent")
    upload_response = upload_avatar(
        client,
        owner.id,
        agent["id"],
        filename="avatar.png",
        content=PNG_BYTES,
        content_type="image/png",
    )
    assert upload_response.status_code == 201

    response = client.get(
        f"/agents/{agent['id']}/avatar/content",
        headers=auth_headers(other.id),
    )
    assert response.status_code == 404


def test_agent_list_and_detail_include_avatar_fields(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="avatar-list-detail")
    agent = create_agent(
        client,
        user.id,
        name="List Detail Avatar Agent",
        avatar_type="emoji",
        avatar_value="🤖",
    )

    list_response = client.get("/agents", headers=auth_headers(user.id))
    assert list_response.status_code == 200
    list_item = next(item for item in list_response.json()["items"] if item["id"] == agent["id"])
    assert list_item["avatar_type"] == "emoji"
    assert list_item["avatar_value"] == "🤖"
    assert list_item["avatar_content_url"] is None

    detail_response = client.get(f"/agents/{agent['id']}", headers=auth_headers(user.id))
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["avatar_type"] == "emoji"
    assert detail_payload["avatar_value"] == "🤖"
