from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.provider_api_keys import get_chat_session_fernet
from app.repositories import agent_repository, session_repository
from app.schemas.agent_chat import ChatMessage
from app.schemas.session import SessionDeleteResponse, SessionDetail, SessionListResponse, SessionSummary


SESSION_TYPE_AGENT = "agent"
SESSION_TYPE_ORCHESTRATOR = "orchestrator"
SESSION_TYPES = {SESSION_TYPE_AGENT, SESSION_TYPE_ORCHESTRATOR}
SESSION_TITLE_FALLBACK = "New chat"
SESSION_TITLE_MAX_LENGTH = 50


def validate_session_type(session_type: str) -> str:
    normalized = str(session_type or "").strip().lower()
    if normalized not in SESSION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session type.",
        )
    return normalized


def _normalize_message_dict(message) -> dict:
    if hasattr(message, "model_dump"):
        payload = message.model_dump()
    elif isinstance(message, dict):
        payload = dict(message)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session message payload.",
        )

    role = payload.get("role")
    content = payload.get("content")
    if role not in {"user", "assistant"} or not isinstance(content, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session message payload.",
        )

    return {"role": role, "content": content}


def normalize_messages(messages: Iterable) -> list[dict]:
    return [_normalize_message_dict(message) for message in messages]


def _supports_session_persistence(db) -> bool:
    return all(hasattr(db, attr) for attr in ("add", "flush", "commit"))


def encode_messages(messages: Iterable) -> str:
    normalized_messages = normalize_messages(messages)
    payload = json.dumps(normalized_messages, ensure_ascii=False, separators=(",", ":"))
    return get_chat_session_fernet().encrypt(payload.encode("utf-8")).decode("utf-8")


def decode_messages(messages_encrypted: str) -> list[ChatMessage]:
    try:
        decrypted = get_chat_session_fernet().decrypt(messages_encrypted.encode("utf-8")).decode("utf-8")
        payload = json.loads(decrypted)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat session data is invalid.",
        ) from exc

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat session data is invalid.",
        )

    messages: list[ChatMessage] = []
    for item in payload:
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Chat session data is invalid.",
            )
        messages.append(ChatMessage.model_validate(item))

    return messages


def build_session_title(messages: Iterable) -> str:
    normalized_messages = normalize_messages(messages)
    first_user_message = next(
        (message.get("content") for message in normalized_messages if message.get("role") == "user"),
        None,
    )
    if not first_user_message:
        return SESSION_TITLE_FALLBACK

    title = " ".join(first_user_message.split())
    if not title:
        return SESSION_TITLE_FALLBACK

    return title[:SESSION_TITLE_MAX_LENGTH]


def build_session_messages(messages: Iterable, assistant_reply: str) -> list[dict]:
    normalized_messages = normalize_messages(messages)
    assistant_message = {"role": "assistant", "content": assistant_reply}
    return [*normalized_messages, assistant_message]


def _resolve_agent_name(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID | None) -> str | None:
    if agent_id is None:
        return None

    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    return agent.name if agent is not None else None


def _build_summary(db: Session, session) -> SessionSummary:
    messages = decode_messages(session.messages_encrypted)
    title = session.title or build_session_title(messages)
    return SessionSummary(
        id=session.id,
        session_type=session.session_type,
        agent_id=session.agent_id,
        agent_name=_resolve_agent_name(db, owner_id=session.user_id, agent_id=session.agent_id),
        title=title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(messages),
    )


def upsert_chat_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_type: str,
    messages: Iterable,
    assistant_reply: str,
    agent_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
) -> SessionSummary:
    normalized_session_type = validate_session_type(session_type)
    stored_messages = build_session_messages(messages, assistant_reply)
    encrypted_messages = encode_messages(stored_messages)

    if not _supports_session_persistence(db):
        synthetic_session_id = session_id or uuid.uuid4()
        return SessionSummary(
            id=synthetic_session_id,
            session_type=normalized_session_type,
            agent_id=agent_id,
            agent_name=None,
            title=build_session_title(messages),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            message_count=len(stored_messages),
        )

    if session_id is None:
        session = session_repository.create_session(
            db,
            user_id=user_id,
            agent_id=agent_id,
            session_type=normalized_session_type,
            title=build_session_title(messages),
            messages_encrypted=encrypted_messages,
        )
    else:
        session = session_repository.get_session(db, session_id, user_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        if session.session_type != normalized_session_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session type mismatch.",
            )
        if session_type == SESSION_TYPE_AGENT and session.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session does not belong to this agent.",
            )

        session.messages_encrypted = encrypted_messages
        if session.title is None:
            session.title = build_session_title(messages)
        if session.agent_id is None and agent_id is not None:
            session.agent_id = agent_id
        db.add(session)
        db.flush()

    db.commit()
    return _build_summary(db, session)


def list_chat_sessions(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> SessionListResponse:
    if not _supports_session_persistence(db):
        return SessionListResponse(sessions=[])

    sessions = session_repository.list_sessions(db, user_id, limit=limit, offset=offset)
    return SessionListResponse(sessions=[_build_summary(db, session) for session in sessions])


def get_chat_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> SessionDetail:
    if not _supports_session_persistence(db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    session = session_repository.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    messages = decode_messages(session.messages_encrypted)
    summary = _build_summary(db, session)
    return SessionDetail(
        **summary.model_dump(),
        messages=messages,
    )


def delete_chat_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> SessionDeleteResponse:
    if not _supports_session_persistence(db):
        return SessionDeleteResponse(success=True)

    deleted = session_repository.delete_session(db, session_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    db.commit()
    return SessionDeleteResponse(success=True)


def load_session_for_owner(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
):
    if not _supports_session_persistence(db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    session = session_repository.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )
    return session
