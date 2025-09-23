from agent.GenerateAgent import GenerateAgent
from agent.prompt import NEXT_DECIDE
from llm import OllamaLLM
from typing import List
from fault_node import FaultNode
from reason_path import ReasonPath

class DecideNextAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = NEXT_DECIDE

    def generate(self, input: str) -> str:
        model = OllamaLLM()
        content = model.predict(input)

        return content

    def output(self, reason_path: ReasonPath, candidate_nodes: List[FaultNode], choices: List[str]) -> str:
        instruction = self.system_instruction.format(
            reason_path=str(reason_path),
            candidate_nodes=str(candidate_nodes),
            information=str(choices),
        )

        node_str = self.generate(instruction)

        return node_str