from app.integrations.model_adapters.base import BaseModelAdapter


class LocalAdapter(BaseModelAdapter):
    def generate_response(self, request: dict) -> dict:
        return {
            "provider_type": "local",
            "model_name": request.get("model_name"),
            "output_text": "Safe local model stub response. No local runtime or Ollama call was made.",
            "stub": True,
        }
