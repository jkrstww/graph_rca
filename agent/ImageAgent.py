from agent.base import BaseAgent
from dashscope import MultiModalConversation
import dashscope 
import os

class ImageAgent(BaseAgent):
    """
    An agent that processes images.
    Inherits from BaseAgent.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize any additional attributes or methods specific to ImageAgent here

    def read_image(self, image_path) -> str:
        """
        Reads an image from the specified path.
        """
        
        messages = [
                        {'role':'user',
                        'content': [{'image': image_path},
                                    {'text': '图中描绘的是什么景象?'}]}]
        response = MultiModalConversation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
            # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
            api_key=os.getenv('QWEN_KEY'),
            model='qwen3-vl-plus',  # 此处以qwen3-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
            messages=messages)
        res = response.output.choices[0].message.content[0]["text"]

        return res
                