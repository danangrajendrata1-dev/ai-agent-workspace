from fastapi import APIRouter, Request

from app.core.config import get_settings


router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
def health_check(request: Request):
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.api_version,
        "request_id": getattr(request.state, "request_id", None),
    }

