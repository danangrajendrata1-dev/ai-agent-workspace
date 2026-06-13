from fastapi import HTTPException, status

from app.integrations.model_adapters import APIProviderAdapter, LocalAdapter, OpenClawAdapter


class ModelRouter:
    def __init__(self):
        self._adapters = {
            "api": APIProviderAdapter(),
            "subscription_oauth": OpenClawAdapter(),
            "local": LocalAdapter(),
        }

    def _get_adapter(self, provider_type: str):
        adapter = self._adapters.get(provider_type)
        if adapter is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider type.",
            )
        return adapter

    def run(self, provider, request: dict) -> dict:
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

        adapter = self._get_adapter(provider.provider_type)
        return adapter.generate_response(request)
