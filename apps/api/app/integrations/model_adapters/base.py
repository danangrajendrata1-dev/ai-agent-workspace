from abc import ABC, abstractmethod


class BaseModelAdapter(ABC):
    @abstractmethod
    def generate_response(self, request: dict) -> dict:
        raise NotImplementedError
