from app.integrations.model_adapters.base import BaseModelAdapter


class APIProviderAdapter(BaseModelAdapter):
    def generate_response(self, request: dict) -> dict:
        return {
            "provider_type": "api",
            "model_name": request.get("model_name"),
            "output_text": "Safe API provider stub response. No external API call was made.",
            "stub": True,
        }
