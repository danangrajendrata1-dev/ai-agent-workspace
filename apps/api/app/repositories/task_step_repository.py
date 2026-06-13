import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task_step import TaskStep


def create_step(db: Session, step_data: dict) -> TaskStep:
    step = TaskStep(**step_data)
    db.add(step)
    db.flush()
    return step


def list_by_task(db: Session, task_id: uuid.UUID) -> list[TaskStep]:
    statement = (
        select(TaskStep)
        .where(TaskStep.task_id == task_id)
        .order_by(TaskStep.step_order.asc())
    )
    return list(db.execute(statement).scalars().all())
