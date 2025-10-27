import os.path
from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_core.document_loaders import BaseLoader
import json
from utils.file_utils import get_encoding
from langchain_ollama import OllamaEmbeddings

embedding_mapping = {
    'ollama': OllamaEmbeddings
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
            emb = embedding_mapping[embedding_method]
            return emb(model=embedding_model)
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

