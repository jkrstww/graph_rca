import json

from agent.GenerateAgent import GenerateAgent
from typing import List
from fault_node import FaultNode
from reason_path import ReasonPath
from llm.ollama_method import OllamaLLM
from agent.prompt import CHOICE_GENERATE

class GenerateChoiceAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = CHOICE_GENERATE

    def generate(self, input: str) -> str:
        model = OllamaLLM()
        content = model.predict(input)

        return content

    def output(self, reason_path: ReasonPath, candidate_nodes: List[FaultNode]) -> List[str]:
        reason_path = str(reason_path)
        candidate_nodes = str(candidate_nodes)
        instruction = self.system_instruction.format(reason_path=reason_path, candidate_nodes=candidate_nodes)

        response = self.generate(instruction)

        questions = json.loads(response)

        choices = List[str]
        for q in questions:
            choices.append(q['question'])

        return choices

