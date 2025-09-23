from vectorbase.base import BaseVectorBase
from typing import Any, Optional
import os
from langchain_chroma import Chroma
from embedding import _OllamaEmbeddings
from dataLoader import CauseEffectLoader


class ChromaVectorBase(BaseVectorBase):
    def __init__(
        self,
        vectorbase_params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super(ChromaVectorBase, self).__init__(vectorbase_params)
        self.db_root_path = './dbs/Chroma'


    def create(self, vectorbase_name: str, embedding_model: str = 'bge-m3', embedding_method = 'ollama'):
        db_path = self.db_root_path + '/' + vectorbase_name

        if os.path.exists(db_path):
            raise KeyError("该数据库已经存在！！！")

        try:
            embedding_function = self.get_embed_func('ollama', 'bge-m3')

            self.vector_store = Chroma(
                embedding_function=embedding_function,
                persist_directory=db_path
            )
            self.config_path = self.db_root_path + '/' + vectorbase_name + '/config.json'
            self.db_path = db_path

            self.embedding_model = embedding_model
            self.embedding_method = embedding_method
            self.vectorbase_type = 'Chroma'
            self.vectorbase_name = vectorbase_name

            self.setConfig()
        except Exception as e:
            raise e


    def open(self, vectorbase_name: str):
        db_path = self.db_root_path + '/' + vectorbase_name

        if not os.path.exists(db_path):
            raise KeyError('数据库不存在')

        self.config_path = self.db_root_path + '/' + vectorbase_name + '/config.json'
        self.getConfig()

        try:
            embedding_function = self.get_embed_func(self.embedding_method, self.embedding_model)
            print(
                db_path
            )

            self.vector_store = Chroma(
                embedding_function=embedding_function,
                persist_directory=db_path
            )

            self.db_path = db_path
        except Exception as e:
            raise e


    def add_document(self, file_path, local_loader) -> None:
        loader = self.data_loader(file_path, local_loader)

        datas = loader.load()

        self.vector_store.add_documents(documents=datas)

    def add_documents(self, files_path, local_loader) -> None:
        if not os.path.isdir(files_path):
            raise KeyError("非文件夹")

        try:
            files = os.listdir(files_path)

            if len(files) == 0:
                raise KeyError("文件夹为空")

            for file_name in files:
                print('加载文档{document}中'.format(document=file_name))
                file_path = files_path + '/' + file_name

                loader = self.data_loader(file_path, local_loader)

                datas = loader.load()

                self.vector_store.add_documents(documents=datas)

        except Exception as e:
            raise e

if __name__ == '__main__':
    chromadb = ChromaVectorBase()
    chromadb.create('transformers')
    chromadb.add_documents(r'D:\Project\Fault_Analyse\backend\output\transformer cause-effect', CauseEffectLoader)

    # chromadb.open('test')
    # data = chromadb.vector_store.get()
    # print(data)
