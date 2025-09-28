from langchain_ollama import ChatOllama
from typing import Any, Optional
from llm import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(
        self,
        model_name: str = 'deepseek-r1:70b',
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(model_name, model_params, **kwargs)

    def predict(self, input: str) -> str:
        llm = ChatOllama(
            model=self.model_name,
        )

        messages = [
            ("human", input)
        ]

        response = llm.invoke(messages)

        return response.content
