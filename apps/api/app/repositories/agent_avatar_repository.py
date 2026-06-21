import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_avatar_asset import AgentAvatarAsset


def get_by_agent_id(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> AgentAvatarAsset | None:
    statement = select(AgentAvatarAsset).where(
        AgentAvatarAsset.user_id == owner_id,
        AgentAvatarAsset.agent_id == agent_id,
    )
    return db.execute(statement).scalar_one_or_none()


def create(db: Session, avatar_data: dict) -> AgentAvatarAsset:
    asset = AgentAvatarAsset(**avatar_data)
    db.add(asset)
    db.flush()
    return asset


def delete_by_agent_id(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> AgentAvatarAsset | None:
    asset = get_by_agent_id(db, owner_id=owner_id, agent_id=agent_id)
    if asset is None:
        return None

    db.execute(delete(AgentAvatarAsset).where(AgentAvatarAsset.id == asset.id))
    db.flush()
    return asset
