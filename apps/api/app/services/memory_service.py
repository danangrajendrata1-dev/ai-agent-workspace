import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import agent_repository, memory_repository
from app.schemas.memory import MemoryCreate, MemoryResponse, MemoryUpdate


BLOCKED_SECRET_PATTERNS = [
    r"(?i)\bsk-[A-Za-z0-9_\-]+\b",
    r"(?i)\bAPI_KEY\s*=",
    r"(?i)\bDATABASE_URL\s*=",
    r"(?i)\bpassword\s*=",
    r"(?i)\bbearer\s+token\b",
]


def serialize_memory(memory) -> MemoryResponse:
    return MemoryResponse(
        id=memory.id,
        owner_id=memory.owner_id,
        agent_id=memory.agent_id,
        memory_type=memory.memory_type,
        title=memory.title,
        content=memory.content,
        visibility_scope=memory.visibility_scope,
        metadata=memory.metadata_json,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        deleted_at=memory.deleted_at,
    )


def validate_no_plaintext_secret(memory_type: str, content: str) -> None:
    lowered = content.strip()
    for pattern in BLOCKED_SECRET_PATTERNS:
        if re.search(pattern, lowered):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Memory content looks like a raw secret and cannot be stored.",
            )

    if memory_type == "sensitive_config_reference":
        forbidden_keywords = ["api key", "oauth token", "database url", "webhook secret", "credential"]
        if any(keyword in lowered.lower() for keyword in forbidden_keywords) and "=" in lowered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sensitive config references must store labels only, not raw secret values.",
            )


def validate_memory_scope(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID | None,
    visibility_scope: str,
) -> None:
    if visibility_scope == "agent" and agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent-scoped memory requires a valid agent_id.",
        )

    if agent_id is not None:
        agent = agent_repository.get_by_id(db, owner_id, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent must belong to the current owner.",
            )


def create_memory(db: Session, *, owner_id: uuid.UUID, payload: MemoryCreate) -> MemoryResponse:
    validate_memory_scope(
        db,
        owner_id=owner_id,
        agent_id=payload.agent_id,
        visibility_scope=payload.visibility_scope,
    )
    validate_no_plaintext_secret(payload.memory_type, payload.content)

    memory = memory_repository.create(
        db,
        {
            "owner_id": owner_id,
            "agent_id": payload.agent_id,
            "memory_type": payload.memory_type,
            "title": payload.title,
            "content": payload.content,
            "visibility_scope": payload.visibility_scope,
            "metadata_json": payload.metadata,
        },
    )
    db.commit()
    db.refresh(memory)
    return serialize_memory(memory)


def list_memories(db: Session, *, owner_id: uuid.UUID) -> list[MemoryResponse]:
    memories = memory_repository.list_by_owner(db, owner_id)
    return [serialize_memory(memory) for memory in memories]


def get_memory(db: Session, *, owner_id: uuid.UUID, memory_id: uuid.UUID) -> MemoryResponse:
    memory = memory_repository.get_by_id(db, owner_id, memory_id)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )
    return serialize_memory(memory)


def update_memory(
    db: Session,
    *,
    owner_id: uuid.UUID,
    memory_id: uuid.UUID,
    payload: MemoryUpdate,
) -> MemoryResponse:
    memory = memory_repository.get_by_id(db, owner_id, memory_id)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    candidate_agent_id = update_data.get("agent_id", memory.agent_id)
    candidate_visibility_scope = update_data.get("visibility_scope", memory.visibility_scope)
    candidate_memory_type = update_data.get("memory_type", memory.memory_type)
    candidate_content = update_data.get("content", memory.content)

    validate_memory_scope(
        db,
        owner_id=owner_id,
        agent_id=candidate_agent_id,
        visibility_scope=candidate_visibility_scope,
    )
    validate_no_plaintext_secret(candidate_memory_type, candidate_content)

    if "metadata" in update_data:
        update_data["metadata_json"] = update_data.pop("metadata")

    memory = memory_repository.update(db, memory, update_data)
    db.commit()
    db.refresh(memory)
    return serialize_memory(memory)


def delete_memory(db: Session, *, owner_id: uuid.UUID, memory_id: uuid.UUID) -> None:
    memory = memory_repository.get_by_id(db, owner_id, memory_id)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )
    memory_repository.soft_delete(db, memory, datetime.now(UTC))
    db.commit()


def list_agent_memories(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> list[MemoryResponse]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    memories = memory_repository.list_by_agent(db, owner_id, agent_id)
    return [serialize_memory(memory) for memory in memories]
