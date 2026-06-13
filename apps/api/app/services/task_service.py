import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.repositories import agent_repository, task_repository, task_step_repository
from app.schemas.task import AgentChatRequest, TaskDetailResponse, TaskResponse, TaskStepResponse
from app.services import agent_runtime_service, log_service


def serialize_step(step) -> TaskStepResponse:
    return TaskStepResponse.model_validate(step)


def serialize_task(task) -> TaskResponse:
    return TaskResponse.model_validate(task)


def serialize_task_detail(task, steps) -> TaskDetailResponse:
    return TaskDetailResponse(
        **TaskResponse.model_validate(task).model_dump(),
        steps=[serialize_step(step) for step in steps],
    )


def create_task_step(db, *, task_id: uuid.UUID, step_order: int, step_name: str, status: str):
    return task_step_repository.create_step(
        db,
        {
            "task_id": task_id,
            "step_order": step_order,
            "step_name": step_name,
            "status": status,
            "input_summary": None,
            "output_summary": None,
            "error_message": None,
        },
    )


def has_completed_step(db, *, task_id: uuid.UUID) -> bool:
    steps = task_step_repository.list_by_task(db, task_id)
    return any(step.step_name == "completed" for step in steps)


def create_agent_chat_task(db, *, owner_id: uuid.UUID, agent_id: uuid.UUID, payload: AgentChatRequest):
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    if agent.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent must be active to accept chat tasks.",
        )

    request_id = payload.request_id or str(uuid.uuid4())
    existing_task = task_repository.get_by_request_id(db, owner_id, request_id)
    if existing_task is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task request_id is already in use.",
        )

    started_at = datetime.now(UTC)
    task = task_repository.create_task(
        db,
        {
            "request_id": request_id,
            "owner_id": owner_id,
            "agent_id": agent.id,
            "input_text": payload.input_text,
            "status": "received",
            "selected_skill_id": None,
            "selected_tool_id": None,
            "final_response": None,
            "error_message": None,
            "started_at": started_at,
            "completed_at": None,
        },
    )
    log_service.record_activity(
        db,
        actor_type="agent",
        actor_id=agent.id,
        request_id=request_id,
        event_type="task.chat_stub_received",
        message="Chat task received for safe runtime orchestration stub.",
        metadata_json={"task_id": str(task.id), "status": "received"},
    )
    try:
        agent_runtime_service.run_agent_chat_stub(
            db,
            owner_id=owner_id,
            task=task,
            agent=agent,
        )
    except HTTPException as exc:
        task_repository.fail_task(
            db,
            task,
            error_message=str(exc.detail),
            completed_at=datetime.now(UTC),
        )
        if not has_completed_step(db, task_id=task.id):
            create_task_step(
                db,
                task_id=task.id,
                step_order=6,
                step_name="completed",
                status="failed",
            )
        log_service.record_activity(
            db,
            actor_type="agent",
            actor_id=agent.id,
            request_id=request_id,
            event_type="task.runtime_stub_failed",
            message="Agent runtime stub failed safely.",
            metadata_json={"task_id": str(task.id), "error": str(exc.detail)},
        )
        db.commit()
        raise
    except Exception:
        safe_error = "Agent runtime stub failed safely."
        task_repository.fail_task(
            db,
            task,
            error_message=safe_error,
            completed_at=datetime.now(UTC),
        )
        if not has_completed_step(db, task_id=task.id):
            create_task_step(
                db,
                task_id=task.id,
                step_order=6,
                step_name="completed",
                status="failed",
            )
        log_service.record_activity(
            db,
            actor_type="agent",
            actor_id=agent.id,
            request_id=request_id,
            event_type="task.runtime_stub_failed",
            message=safe_error,
            metadata_json={"task_id": str(task.id)},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error,
        )

    db.commit()
    db.refresh(task)
    task_steps = task_step_repository.list_by_task(db, task.id)
    return serialize_task_detail(task, task_steps)


def list_tasks(db, *, owner_id: uuid.UUID) -> list[TaskResponse]:
    tasks = task_repository.list_by_owner(db, owner_id)
    return [serialize_task(task) for task in tasks]


def get_task(db, *, owner_id: uuid.UUID, task_id: uuid.UUID) -> TaskDetailResponse:
    task = task_repository.get_by_id(db, owner_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    steps = task_step_repository.list_by_task(db, task.id)
    return serialize_task_detail(task, steps)


def list_agent_tasks(db, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> list[TaskResponse]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    tasks = task_repository.list_by_agent(db, owner_id, agent_id)
    return [serialize_task(task) for task in tasks]
