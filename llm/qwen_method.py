from langchain_ollama import ChatOllama
from typing import Any, Optional
from llm import BaseLLM
from openai import OpenAI


class QwenLLM(BaseLLM):
    def __init__(
        self,
        model_name: str = 'qwen-plus',
        model_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(model_name, model_params, **kwargs)

    def predict(self, input: str) -> str:
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key='sk-a780e4a78aa0401ea9d059e0f583ba1f',
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model=self.model_name,
            messages=[
                {"role": "system", "content": "根据提供的指令执行任务"},
                {"role": "user", "content": input},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
        )

        return completion.choices[0].message.content

if __name__ == '__main__':
    llm = QwenLLM()
    ret = llm.predict('告诉我你是谁')
    print(ret)

