import os.path
from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_core.document_loaders import BaseLoader
import json
from utils.file_utils import get_encoding
from langchain_ollama import OllamaEmbeddings

from config import QWEN_KEY

import os
from typing import List, Optional
from openai import OpenAI
from langchain.embeddings.base import Embeddings

class QwenEmbeddings(Embeddings):
    """使用OpenAI客户端调用Qwen DashScope Embeddings API"""
    
    def __init__(
        self, 
        model: str = "text-embedding-v4",
        api_key: str = QWEN_KEY,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        dimensions: int = 1024,
        encoding_format: str = "float",
        max_retries: int = 3
    ):
        self.model = model
        self.dimensions = dimensions
        self.encoding_format = encoding_format
        self.max_retries = max_retries
        
        # 获取API密钥
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("DashScope API key is required. Set DASHSCOPE_API_KEY environment variable or pass api_key parameter.")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
    
    def _create_embedding(self, texts: List[str]) -> List[List[float]]:
        """使用OpenAI客户端创建嵌入向量"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
                encoding_format=self.encoding_format
            )

            # 提取嵌入向量
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            # 返回默认向量作为降级方案
            default_embedding = [0.0] * self.dimensions
            return [default_embedding] * len(texts)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档生成嵌入向量"""
        if not texts:
            return []
        
        # 分批处理以避免请求过大
        batch_size = 8  # OpenAI兼容API通常支持16个文本每批次
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 重试机制
            for attempt in range(self.max_retries):
                try:
                    batch_embeddings = self._create_embedding(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                    break  # 成功则跳出重试循环
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        print(f"Failed to embed batch {i} after {self.max_retries} attempts: {e}")
                        # 最后一次重试失败，创建默认向量
                        embedding_dim = self.dimensions
                        for _ in batch_texts:
                            all_embeddings.append([0.0] * embedding_dim)
                    else:
                        print(f"Attempt {attempt + 1} failed for batch {i}, retrying...")
                        continue
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """为查询文本生成嵌入向量"""
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else [0.0] * self.dimensions


embedding_mapping = {
    'ollama': OllamaEmbeddings,
    'qwen': QwenEmbeddings
}

class BaseVectorBase(ABC):
    def __init__(
        self,
        vectorbase_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.vectorbase_name = ''
        self.vectorbase_params = vectorbase_params or {}
        self.db_root_path = ''
        self.db_path = ''
        self.config_path = ''
        self.vectorbase_type = ''
        self.embedding_model = ''
        self.embedding_method = ''

    def data_loader(self, file_path, localLoader: BaseLoader):
        if not os.path.exists(file_path):
            raise KeyError("文件不存在")

        loader = localLoader(
            file_path=file_path
        )

        return loader

    # 读取数据库的配置，主要是创建数据库时embedding使用的模型名称，embedding使用的方法
    def getConfig(self):
        try:
            with open(self.config_path, 'r', encoding=get_encoding(self.config_path)) as f:
                config = json.load(f)
            f.close()

            self.embedding_model = config['embedding_model']
            self.embedding_method = config['embedding_method']
            self.vectorbase_type = config['vectorbase_type']
            self.vectorbase_name = config['vectorbase_name']

        except Exception as e:
            raise e

    def setConfig(self):
        try:
            data = {
                'embedding_model': self.embedding_model,
                'embedding_method': self.embedding_method,
                'vectorbase_type': self.vectorbase_type,
                'vectorbase_name': self.vectorbase_name,
            }

            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            file.close()
        except Exception as e:
            raise e

    def get_embed_func(self, embedding_method: str, embedding_model: str):
        if embedding_method not in embedding_mapping:
            raise KeyError("暂时不支持该类模型")

        try:
            emb_class = embedding_mapping[embedding_method]

            return emb_class(model=embedding_model)
        except Exception as e:
            raise e

    @abstractmethod
    def create(self, name: str, embedding_model: Optional[str] = None) -> str:
        """
        """

    @abstractmethod
    def open(self):
        """

        :return:
        """

    @abstractmethod
    def add_document(self, file_path: str, data_loader: BaseLoader):
        """

        :return:
        """



    # @abstractmethod
    # def search(self, input: str) -> str:
    #     """
    #     :param input:
    #     :return: related chunks
    #     """
    #


