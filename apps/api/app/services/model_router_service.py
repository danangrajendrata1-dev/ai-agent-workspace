from time import perf_counter

from fastapi import HTTPException, status

from app.repositories import agent_repository, model_provider_repository, task_repository
from app.schemas.model_router import ModelRouterRequest, ModelRouterResponse
from app.services import log_service


MODEL_ROUTER_BLOCK_REASON = "Model generation is disabled in this release."


def get_provider_for_agent(db, *, owner_id, agent_id):
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    if agent.default_model_provider_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent does not have a default model provider.",
        )
    provider = model_provider_repository.get_by_id(db, agent.default_model_provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model provider not found.",
        )
    return provider


def run_model_stub(db, *, owner_id, payload: ModelRouterRequest, auto_commit: bool = True) -> ModelRouterResponse:
    provider = model_provider_repository.get_by_id(db, payload.provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model provider not found.",
        )
    if provider.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be active.",
        )
    if provider.provider_type == "subscription_oauth" and provider.is_private is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenClaw provider must remain private.",
        )
    if provider.provider_type not in {"api", "subscription_oauth", "local"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider type.",
        )

    if payload.agent_id is not None:
        agent = agent_repository.get_by_id(db, owner_id, payload.agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found.",
            )

    if payload.task_id is not None:
        task = task_repository.get_by_id(db, owner_id, payload.task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

    start = perf_counter()
    latency_ms = int((perf_counter() - start) * 1000)
    response = {
        "provider_type": provider.provider_type,
        "model_name": payload.model_name or provider.default_model,
        "output_text": "Safe model stub response. No model generation was performed.",
        "stub": True,
    }

    log_service.record_model_usage(
        db,
        provider_id=provider.id,
        agent_id=payload.agent_id,
        task_id=payload.task_id,
        model_name=response.get("model_name"),
        prompt_tokens=0,
        completion_tokens=0,
        estimated_cost=0,
        latency_ms=latency_ms,
        status="blocked",
        error_message=MODEL_ROUTER_BLOCK_REASON,
    )
    if auto_commit:
        db.commit()

    return ModelRouterResponse(
        provider_id=provider.id,
        provider_type=response["provider_type"],
        model_name=response.get("model_name"),
        output_text=response["output_text"],
        stub=response["stub"],
        latency_ms=latency_ms,
    )
