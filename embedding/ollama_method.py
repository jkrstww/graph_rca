from typing import List
from embedding import BaseEmb
from langchain_ollama import OllamaEmbeddings


class OllamaEmb(BaseEmb):
    def __init__(self, model_name: str = 'bge-m3', **kwargs):
        super().__init__(model_name=model_name, **kwargs)

        # 预先创建会话以提高效率（如果需要）
        self.model_name = model_name

    def get_emb(self, text: str) -> List[float]:
        """使用Ollama API获取文本的嵌入向量"""
        try:
            # 直接调用Ollama的API
            embedding_model = OllamaEmbeddings(
                model=self.model_name
            )

            embedding = embedding_model.embed_query(text)

            return embedding
        except Exception as e:
            print(f"获取嵌入向量时出错: {e}")
            return []

    def embedding_function(self):
        return OllamaEmbeddings(
            model=self.model_name
        )

    def __call__(self, text: str) -> List[float]:
        """使实例可调用"""
        return self.get_emb(text)

class _OllamaEmbeddings(OllamaEmbeddings):
    def __init__(self, model: str = 'bge-m3'):
        super(_OllamaEmbeddings, self).__init__(model=model)

if __name__ == '__main__':
    # 创建嵌入向量生成器实例
    embedding_model = OllamaEmb()

    # 获取文本的嵌入向量
    result = embedding_model.get_emb('你好')
    print(result)
