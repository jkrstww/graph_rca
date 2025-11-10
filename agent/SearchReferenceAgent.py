from agent.GenerateAgent import GenerateAgent
from typing import List
import os
import ast
from llm import OllamaLLM, QwenLLM
from agent.prompt import SEARCH_REFERENCE
from config import PROJECT_ROOT

class SearchReferenceAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = SEARCH_REFERENCE
        self.references = self.get_references()
        

    def generate(self, input: str) -> str:
        # model = OllamaLLM(model_name='llama3.2')
        model = QwenLLM(model_name='qwen-plus')
        reference_list = str(self.references)
        content = model.predict(self.system_instruction.format(user_query=input, reference_list=reference_list))

        return content

    def output(self, user_query: str) -> List[str]:
        content = self.generate(user_query)
        list = ast.literal_eval(content)

        return list
    
    def get_references(self) -> List[str]:
        reference_path = PROJECT_ROOT + '/static/references'
        
        reference_list = os.listdir(reference_path)

        return reference_list
    
if __name__ == '__main__':
    agent = SearchReferenceAgent()
    list = agent.output('变压器发热')