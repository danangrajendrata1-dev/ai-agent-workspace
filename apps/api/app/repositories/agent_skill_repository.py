import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.agent_skill import AgentSkill


def assign_skill_to_agent(db: Session, assignment_data: dict) -> AgentSkill:
    assignment = AgentSkill(**assignment_data)
    db.add(assignment)
    db.flush()
    return assignment


def unassign_skill_from_agent(db: Session, assignment: AgentSkill) -> None:
    db.delete(assignment)
    db.flush()


def list_agent_skills(db: Session, agent_id: uuid.UUID) -> list[AgentSkill]:
    statement = (
        select(AgentSkill)
        .options(joinedload(AgentSkill.skill))
        .where(AgentSkill.agent_id == agent_id)
        .order_by(AgentSkill.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def get_assignment(db: Session, agent_id: uuid.UUID, skill_id: uuid.UUID) -> AgentSkill | None:
    statement = (
        select(AgentSkill)
        .options(joinedload(AgentSkill.skill))
        .where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )
    return db.execute(statement).scalar_one_or_none()
