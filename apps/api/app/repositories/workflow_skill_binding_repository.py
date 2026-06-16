import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow_skill_template_binding import WorkflowSkillTemplateBinding


def create_binding(
    db: Session,
    *,
    user_id: uuid.UUID,
    skill_id: uuid.UUID,
    template_id: str,
    template_version: str,
) -> WorkflowSkillTemplateBinding:
    binding = WorkflowSkillTemplateBinding(
        user_id=user_id,
        skill_id=skill_id,
        template_id=template_id,
        template_version=template_version,
    )
    db.add(binding)
    db.flush()
    return binding


def get_binding(
    db: Session,
    *,
    user_id: uuid.UUID,
    skill_id: uuid.UUID,
    template_id: str,
) -> WorkflowSkillTemplateBinding | None:
    statement = select(WorkflowSkillTemplateBinding).where(
        WorkflowSkillTemplateBinding.user_id == user_id,
        WorkflowSkillTemplateBinding.skill_id == skill_id,
        WorkflowSkillTemplateBinding.template_id == template_id,
    )
    return db.execute(statement).scalar_one_or_none()


def get_binding_by_id(
    db: Session,
    *,
    user_id: uuid.UUID,
    binding_id: uuid.UUID,
) -> WorkflowSkillTemplateBinding | None:
    statement = select(WorkflowSkillTemplateBinding).where(
        WorkflowSkillTemplateBinding.user_id == user_id,
        WorkflowSkillTemplateBinding.id == binding_id,
    )
    return db.execute(statement).scalar_one_or_none()


def list_bindings(db: Session, *, user_id: uuid.UUID) -> list[WorkflowSkillTemplateBinding]:
    statement = (
        select(WorkflowSkillTemplateBinding)
        .where(WorkflowSkillTemplateBinding.user_id == user_id)
        .order_by(WorkflowSkillTemplateBinding.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def delete_binding(db: Session, *, binding: WorkflowSkillTemplateBinding) -> None:
    db.delete(binding)
    db.flush()
