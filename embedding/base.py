from abc import ABC, abstractmethod
from typing import List, Any, Optional
from langchain_ollama import OllamaEmbeddings

class BaseEmb(ABC):
    def __init__(
        self,
        model_name: str,
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.model_name = model_name
        self.model_params = model_params or {}

    def emb_func(self):
        pass


    @abstractmethod
    def get_emb(self, input: str) -> List[float]:
        """Sends a text input to the embedding model and retrieves the embedding.

        Args:
            input (str): Text sent to the embedding model

        Returns:
            List[float]: The embedding vector from the model.
        """
        pass

if __name__ == '__main__':
    emb = BaseEmb