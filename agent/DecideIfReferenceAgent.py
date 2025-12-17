from agent.GenerateAgent import GenerateAgent
from llm import OllamaLLM, QwenLLM
from agent.prompt import IF_REFERENCE

class DecideIfReferenceAgent(GenerateAgent):
    def __init__(self):
        super().__init__()
        self.system_instruction = IF_REFERENCE

    def generate(self, input: str) -> str:
        # model = OllamaLLM(model_name='llama3.2')
        model = QwenLLM(model_name='qwen-plus')
        content = model.predict(input)

        return content

    def output(self, content: str) -> bool:

        try:
            instruction = self.system_instruction.format(input=content)
        except Exception as e:
            print(e)

        response = self.generate(instruction)

        return 'Y' in response or '是' in response