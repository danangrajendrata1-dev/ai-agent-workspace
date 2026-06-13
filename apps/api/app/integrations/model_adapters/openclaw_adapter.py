from app.integrations.model_adapters.base import BaseModelAdapter


class OpenClawAdapter(BaseModelAdapter):
    def generate_response(self, request: dict) -> dict:
        return {
            "provider_type": "subscription_oauth",
            "model_name": request.get("model_name"),
            "output_text": "Safe OpenClaw stub response. No OpenClaw or OAuth-backed call was made.",
            "stub": True,
        }
