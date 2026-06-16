import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow_execution import WorkflowExecution


def create_execution(db: Session, execution_data: dict) -> WorkflowExecution:
    execution = WorkflowExecution(**execution_data)
    db.add(execution)
    db.flush()
    return execution


def list_executions(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[WorkflowExecution]:
    statement = (
        select(WorkflowExecution)
        .where(WorkflowExecution.user_id == user_id)
        .order_by(WorkflowExecution.executed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(statement).scalars().all())
