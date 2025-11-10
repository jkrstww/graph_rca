import json

from agent.GenerateAgent import GenerateAgent
from typing import List
from fault_node import FaultNode
from reason_path import ReasonPath
from llm import OllamaLLM, QwenLLM
from agent.prompt import CHOICE_GENERATE

class GenerateChoiceAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = CHOICE_GENERATE

    def generate(self, input: str) -> str:
        # model = OllamaLLM(model_name='llama3.2')
        model = QwenLLM(model_name='qwen-plus')
        content = model.predict(input)

        return content

    def output(self, reason_path: ReasonPath, candidate_nodes: List[FaultNode]) -> List[str]:
        reason_path_str = str(reason_path)
        candidate_nodes_str = str(candidate_nodes)
        try:
            instruction = self.system_instruction.format(reason_path=reason_path_str, candidate_nodes=candidate_nodes_str)
        except Exception as e:
            print(e)

        response = self.generate(instruction)

        questions = json.loads(response)

        choices: List[str] = []
        for q in questions:
            choices.append(q['question'])

        return choices

