import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task


def create_task(db: Session, task_data: dict) -> Task:
    task = Task(**task_data)
    db.add(task)
    db.flush()
    return task


def get_by_id(db: Session, owner_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
    statement = select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    return db.execute(statement).scalar_one_or_none()


def get_by_request_id(db: Session, owner_id: uuid.UUID, request_id: str) -> Task | None:
    statement = select(Task).where(Task.request_id == request_id, Task.owner_id == owner_id)
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[Task]:
    statement = select(Task).where(Task.owner_id == owner_id).order_by(Task.created_at.desc())
    return list(db.execute(statement).scalars().all())


def list_by_agent(db: Session, owner_id: uuid.UUID, agent_id: uuid.UUID) -> list[Task]:
    statement = (
        select(Task)
        .where(Task.owner_id == owner_id, Task.agent_id == agent_id)
        .order_by(Task.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def update_status(db: Session, task: Task, status: str) -> Task:
    task.status = status
    db.add(task)
    db.flush()
    return task


def complete_task(
    db: Session,
    task: Task,
    *,
    final_response: str,
    completed_at,
) -> Task:
    task.status = "completed"
    task.final_response = final_response
    task.completed_at = completed_at
    db.add(task)
    db.flush()
    return task


def fail_task(db: Session, task: Task, *, error_message: str, completed_at) -> Task:
    task.status = "failed"
    task.error_message = error_message
    task.completed_at = completed_at
    db.add(task)
    db.flush()
    return task
