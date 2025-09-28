from agent.GenerateAgent import GenerateAgent
from llm.ollama_method import OllamaLLM

class CauseExtractAgent(GenerateAgent):
    def __init__(self):
        super().__init__()

    def generate(self):
        llm = OllamaLLM()