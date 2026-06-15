from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.middleware import RequestIDMiddleware
from app.routes import (
    agents,
    approvals,
    auth,
    github_imports,
    health,
    handoff_drafts,
    logs,
    memories,
    model_provider_keys,
    model_provider_settings,
    model_providers,
    model_router,
    n8n_workflows,
    skills,
    tasks,
    tool_execution,
    tools,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(model_provider_settings.router)
app.include_router(model_provider_keys.router)
app.include_router(model_providers.router)
app.include_router(agents.router)
app.include_router(skills.router)
app.include_router(github_imports.router)
app.include_router(handoff_drafts.router)
app.include_router(tools.router)
app.include_router(memories.router)
app.include_router(tasks.router)
app.include_router(approvals.router)
app.include_router(logs.router)
app.include_router(model_router.router)
app.include_router(tool_execution.router)
app.include_router(n8n_workflows.router)
