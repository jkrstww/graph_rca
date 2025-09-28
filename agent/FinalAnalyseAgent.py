from agent.GenerateAgent import GenerateAgent
from typing import List
from reason_path import ReasonPath
from llm.ollama_method import OllamaLLM
from agent.prompt import FINAL_ANALYSE

class FinalAnalyseAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = FINAL_ANALYSE

    def generate(self, input: str) -> str:
        model = OllamaLLM(model_name='llama3.2')
        content = model.predict(self.system_instruction.format(reason_paths=input))

        return content

    def output(self, reason_paths: List[ReasonPath]) -> str:
        content = self.generate(str(reason_paths))

        return content