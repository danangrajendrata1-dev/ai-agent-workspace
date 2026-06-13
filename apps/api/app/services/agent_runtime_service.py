import json
import re
import uuid
from datetime import UTC, datetime

from app.repositories import (
    agent_skill_repository,
    agent_tool_repository,
    memory_repository,
    task_repository,
    task_step_repository,
)
from app.schemas.model_router import ModelRouterRequest
from app.services import log_service, model_router_service


SENSITIVE_TITLE_PATTERNS = [
    r"(?i)\bsk-[A-Za-z0-9_\-]+\b",
    r"(?i)^bearer\s+.+",
    r"(?i)\bapi[_-]?key\b",
    r"(?i)\bdatabase_url\b",
    r"(?i)\bpassword\b",
    r"(?i)\bsecret\b",
    r"(?i)\bauthorization\b",
    r"(?i)\btoken\b",
]


def create_runtime_step(
    db,
    *,
    task_id: uuid.UUID,
    step_order: int,
    step_name: str,
    status: str,
    input_summary: str | None = None,
    output_summary: str | None = None,
    error_message: str | None = None,
):
    return task_step_repository.create_step(
        db,
        {
            "task_id": task_id,
            "step_order": step_order,
            "step_name": step_name,
            "status": status,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "error_message": error_message,
        },
    )


def sanitize_memory_title(title: str) -> str:
    masked_title = log_service.mask_sensitive_data(title)
    if masked_title != title:
        return "[masked sensitive title]"

    if any(re.search(pattern, title) for pattern in SENSITIVE_TITLE_PATTERNS):
        return "[masked sensitive title]"

    return title


def load_memory_context_stub(db, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> dict:
    memories = memory_repository.list_by_owner(db, owner_id)
    selected_memories = []
    for memory in memories:
        if memory.visibility_scope in {"global", "private"} and memory.agent_id is None:
            selected_memories.append(memory)
            continue
        if memory.visibility_scope == "agent" and memory.agent_id == agent_id:
            selected_memories.append(memory)

    items = [
        {
            "id": str(memory.id),
            "title": sanitize_memory_title(memory.title),
            "memory_type": memory.memory_type,
            "visibility_scope": memory.visibility_scope,
        }
        for memory in selected_memories
    ]
    return {
        "count": len(items),
        "items": items,
        "titles": [item["title"] for item in items],
    }


def load_skill_context_stub(db, *, agent_id: uuid.UUID) -> dict:
    assignments = agent_skill_repository.list_agent_skills(db, agent_id)
    items = []
    for assignment in assignments:
        skill = assignment.skill
        if not assignment.is_enabled or skill is None:
            continue
        if skill.deleted_at is not None or skill.status != "active":
            continue
        items.append(
            {
                "id": str(skill.id),
                "name": skill.name,
                "slug": skill.slug,
                "risk_level": skill.risk_level,
                "source_type": skill.source_type,
            }
        )

    return {
        "count": len(items),
        "items": items,
        "names": [item["name"] for item in items],
    }


def load_tool_context_stub(db, *, agent_id: uuid.UUID) -> dict:
    assignments = agent_tool_repository.list_agent_tools(db, agent_id)
    items = []
    for assignment in assignments:
        tool = assignment.tool
        if tool is None or not assignment.is_enabled:
            continue
        if assignment.permission_mode != "allow":
            continue
        if tool.deleted_at is not None or tool.status != "active":
            continue
        items.append(
            {
                "id": str(tool.id),
                "name": tool.name,
                "slug": tool.slug,
                "risk_level": tool.risk_level,
                "tool_type": tool.tool_type,
                "approval_required": tool.approval_required,
            }
        )

    return {
        "count": len(items),
        "items": items,
        "names": [item["name"] for item in items],
    }


def build_safe_stub_response(
    *,
    agent,
    memory_context: dict,
    skill_context: dict,
    tool_context: dict,
    model_stub_result,
) -> str:
    response_payload = {
        "mode": "agent_runtime_stub",
        "execution_performed": False,
        "summary": (
            "Agent runtime stub completed safely. Context was inspected, but no real "
            "model call, skill execution, tool execution, approval execution, or external action occurred."
        ),
        "agent": {
            "id": str(agent.id),
            "name": agent.name,
            "slug": agent.slug,
            "status": agent.status,
        },
        "inspected_context": {
            "memory_count": memory_context["count"],
            "memory_titles": memory_context["titles"],
            "skill_count": skill_context["count"],
            "skill_names": skill_context["names"],
            "tool_count": tool_context["count"],
            "tools": [
                {
                    "name": item["name"],
                    "slug": item["slug"],
                    "risk_level": item["risk_level"],
                }
                for item in tool_context["items"]
            ],
            "model_router_stub": (
                {
                    "used": True,
                    "provider_id": str(model_stub_result.provider_id),
                    "provider_type": model_stub_result.provider_type,
                    "model_name": model_stub_result.model_name,
                    "stub": model_stub_result.stub,
                }
                if model_stub_result is not None
                else {
                    "used": False,
                    "reason": "No default model provider configured for this agent.",
                }
            ),
        },
        "notes": [
            "Memories were summarized safely by count and title only.",
            "Skills were treated as text references only.",
            "Tools were treated as metadata and permission references only.",
            "No n8n workflow, GitHub imported tool, terminal command, or external system was executed.",
        ],
    }
    return json.dumps(response_payload, indent=2)


def run_agent_chat_stub(db, *, owner_id: uuid.UUID, task, agent) -> dict:
    safe_prompt_summary = log_service.mask_sensitive_data(task.input_text)

    create_runtime_step(
        db,
        task_id=task.id,
        step_order=1,
        step_name="received",
        status="success",
        input_summary="Chat request accepted for safe runtime stub.",
        output_summary=f"request_id={task.request_id}",
    )

    memory_context = load_memory_context_stub(db, owner_id=owner_id, agent_id=agent.id)
    create_runtime_step(
        db,
        task_id=task.id,
        step_order=2,
        step_name="loading_memory",
        status="success",
        input_summary="Loading owner and agent-scoped memories safely.",
        output_summary=f"Loaded {memory_context['count']} memory summaries.",
    )

    skill_context = load_skill_context_stub(db, agent_id=agent.id)
    create_runtime_step(
        db,
        task_id=task.id,
        step_order=3,
        step_name="selecting_skill",
        status="success",
        input_summary="Inspecting assigned active skills as text references.",
        output_summary=f"Found {skill_context['count']} active assigned skills.",
    )

    tool_context = load_tool_context_stub(db, agent_id=agent.id)
    create_runtime_step(
        db,
        task_id=task.id,
        step_order=4,
        step_name="selecting_tool",
        status="success",
        input_summary="Inspecting assigned active allowed tools as metadata references.",
        output_summary=f"Found {tool_context['count']} active allowed tools.",
    )

    model_stub_result = None
    if agent.default_model_provider_id is None:
        create_runtime_step(
            db,
            task_id=task.id,
            step_order=5,
            step_name="model_router_stub",
            status="skipped",
            input_summary="Model router stub check.",
            output_summary="Skipped because no default model provider is configured.",
        )
    else:
        model_stub_result = model_router_service.run_model_stub(
            db,
            owner_id=owner_id,
            payload=ModelRouterRequest(
                provider_id=agent.default_model_provider_id,
                agent_id=agent.id,
                task_id=task.id,
                model_name=agent.default_model_name,
                prompt=safe_prompt_summary,
            ),
            auto_commit=False,
        )
        create_runtime_step(
            db,
            task_id=task.id,
            step_order=5,
            step_name="model_router_stub",
            status="success",
            input_summary="Model router stub invoked with safe prompt summary only.",
            output_summary=f"Stub provider {model_stub_result.provider_type} responded without external call.",
        )

    final_response = build_safe_stub_response(
        agent=agent,
        memory_context=memory_context,
        skill_context=skill_context,
        tool_context=tool_context,
        model_stub_result=model_stub_result,
    )

    task_repository.complete_task(
        db,
        task,
        final_response=final_response,
        completed_at=datetime.now(UTC),
    )
    create_runtime_step(
        db,
        task_id=task.id,
        step_order=6,
        step_name="completed",
        status="success",
        input_summary="Finalizing safe runtime orchestration stub.",
        output_summary="Stub runtime completed without external execution.",
    )

    log_service.record_activity(
        db,
        actor_type="agent",
        actor_id=agent.id,
        request_id=task.request_id,
        event_type="task.runtime_stub_completed",
        message="Agent runtime stub completed safely.",
        metadata_json={
            "task_id": str(task.id),
            "memory_count": memory_context["count"],
            "skill_count": skill_context["count"],
            "tool_count": tool_context["count"],
            "model_router_stub_used": model_stub_result is not None,
        },
    )

    return {
        "memory_context": memory_context,
        "skill_context": skill_context,
        "tool_context": tool_context,
        "model_stub_result": model_stub_result,
        "final_response": final_response,
    }
