from agent import BaseAgent
from abc import abstractmethod
from typing import List

class GenerateAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def generate(self, input: str) -> str:
        pass

    @abstractmethod
    def output(self, **kwargs):
        pass