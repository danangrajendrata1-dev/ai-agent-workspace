from app.schemas.runtime import RuntimeReadinessResponse


def get_runtime_readiness() -> RuntimeReadinessResponse:
    return RuntimeReadinessResponse(
        status="disabled",
        message="Agent runtime execution is not enabled yet. This endpoint is a safe readiness stub.",
        runtime_execution_enabled=False,
        tool_execution_enabled=False,
        model_raw_generation_enabled=False,
        requires_future_safety_review=True,
        docs_path="docs/agent-runtime-readiness.md",
    )
