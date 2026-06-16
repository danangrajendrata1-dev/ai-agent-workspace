import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    agent_id: uuid.UUID | None,
    session_type: str,
    title: str | None,
    messages_encrypted: str,
) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        agent_id=agent_id,
        session_type=session_type,
        title=title,
        messages_encrypted=messages_encrypted,
    )
    db.add(session)
    db.flush()
    db.refresh(session)
    return session


def list_sessions(db: Session, user_id: uuid.UUID, *, limit: int = 20, offset: int = 0) -> list[ChatSession]:
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars().all())


def get_session(db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
    statement = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    )
    return db.execute(statement).scalar_one_or_none()


def update_session_messages(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    messages_encrypted: str,
) -> ChatSession | None:
    session = get_session(db, session_id, user_id)
    if session is None:
        return None

    session.messages_encrypted = messages_encrypted
    db.add(session)
    db.flush()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    session = get_session(db, session_id, user_id)
    if session is None:
        return False

    db.delete(session)
    db.flush()
    return True
