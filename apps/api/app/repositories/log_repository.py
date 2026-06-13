import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.models.model_usage_log import ModelUsageLog
from app.models.task import Task
from app.models.tool_call import ToolCall


def create_activity_log(db: Session, log_data: dict) -> ActivityLog:
    log = ActivityLog(**log_data)
    db.add(log)
    db.flush()
    return log


def create_audit_log(db: Session, log_data: dict) -> AuditLog:
    log = AuditLog(**log_data)
    db.add(log)
    db.flush()
    return log


def create_tool_call(db: Session, log_data: dict) -> ToolCall:
    log = ToolCall(**log_data)
    db.add(log)
    db.flush()
    return log


def create_model_usage_log(db: Session, log_data: dict) -> ModelUsageLog:
    log = ModelUsageLog(**log_data)
    db.add(log)
    db.flush()
    return log


def list_activity_logs(db: Session, *, request_id=None, event_type=None, limit=50) -> list[ActivityLog]:
    statement = select(ActivityLog).order_by(ActivityLog.created_at.desc())
    if request_id:
        statement = statement.where(ActivityLog.request_id == request_id)
    if event_type:
        statement = statement.where(ActivityLog.event_type == event_type)
    statement = statement.limit(limit)
    return list(db.execute(statement).scalars().all())


def list_audit_logs(db: Session, *, user_id=None, entity_type=None, limit=50) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    if user_id:
        statement = statement.where(AuditLog.user_id == user_id)
    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)
    statement = statement.limit(limit)
    return list(db.execute(statement).scalars().all())


def list_tool_calls(
    db: Session,
    *,
    owner_id: uuid.UUID,
    task_id=None,
    tool_id=None,
    status=None,
    limit=50,
) -> list[ToolCall]:
    statement = (
        select(ToolCall)
        .join(Task, ToolCall.task_id == Task.id)
        .join(Agent, ToolCall.agent_id == Agent.id)
        .where(or_(Task.owner_id == owner_id, Agent.owner_id == owner_id))
        .order_by(ToolCall.created_at.desc())
    )
    if task_id:
        statement = statement.where(ToolCall.task_id == task_id)
    if tool_id:
        statement = statement.where(ToolCall.tool_id == tool_id)
    if status:
        statement = statement.where(ToolCall.status == status)
    statement = statement.limit(limit)
    return list(db.execute(statement).scalars().all())


def list_model_usage_logs(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider_id=None,
    agent_id=None,
    task_id=None,
    status=None,
    limit=50,
) -> list[ModelUsageLog]:
    statement = (
        select(ModelUsageLog)
        .outerjoin(Task, ModelUsageLog.task_id == Task.id)
        .outerjoin(Agent, ModelUsageLog.agent_id == Agent.id)
        .where(or_(Task.owner_id == owner_id, Agent.owner_id == owner_id))
        .order_by(ModelUsageLog.created_at.desc())
    )
    if provider_id:
        statement = statement.where(ModelUsageLog.provider_id == provider_id)
    if agent_id:
        statement = statement.where(ModelUsageLog.agent_id == agent_id)
    if task_id:
        statement = statement.where(ModelUsageLog.task_id == task_id)
    if status:
        statement = statement.where(ModelUsageLog.status == status)
    statement = statement.limit(limit)
    return list(db.execute(statement).scalars().all())


def get_activity_log(db: Session, log_id: uuid.UUID) -> ActivityLog | None:
    return db.execute(select(ActivityLog).where(ActivityLog.id == log_id)).scalar_one_or_none()


def get_audit_log(db: Session, log_id: uuid.UUID) -> AuditLog | None:
    return db.execute(select(AuditLog).where(AuditLog.id == log_id)).scalar_one_or_none()


def get_tool_call(db: Session, *, owner_id: uuid.UUID, tool_call_id: uuid.UUID) -> ToolCall | None:
    statement = (
        select(ToolCall)
        .join(Task, ToolCall.task_id == Task.id)
        .join(Agent, ToolCall.agent_id == Agent.id)
        .where(ToolCall.id == tool_call_id)
        .where(or_(Task.owner_id == owner_id, Agent.owner_id == owner_id))
    )
    return db.execute(statement).scalar_one_or_none()


def get_model_usage_log(
    db: Session,
    *,
    owner_id: uuid.UUID,
    usage_log_id: uuid.UUID,
) -> ModelUsageLog | None:
    statement = (
        select(ModelUsageLog)
        .outerjoin(Task, ModelUsageLog.task_id == Task.id)
        .outerjoin(Agent, ModelUsageLog.agent_id == Agent.id)
        .where(ModelUsageLog.id == usage_log_id)
        .where(or_(Task.owner_id == owner_id, Agent.owner_id == owner_id))
    )
    return db.execute(statement).scalar_one_or_none()
