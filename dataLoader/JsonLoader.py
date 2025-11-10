from typing import AsyncIterator, Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

import json
import os

from utils.file_utils import get_encoding

class CauseEffectLoader(BaseLoader):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.encoding = get_encoding(self.file_path)

    def lazy_load(self) -> Iterator[Document]:
        with open(self.file_path, encoding=self.encoding) as f:
            datas = json.load(f)
            for data in datas:
                yield Document(
                    page_content=data['sentence'],
                    metadata={"cause_effect": str(data['cause-effect']), "source": self.file_path},
                )
    async def alazy_load(
        self,
    ) -> AsyncIterator[Document]:
        import aiofiles

        async with aiofiles.open(self.file_path, encoding=self.encoding) as f:
            content = await f.read()
            async for data in json.loads(content):
                yield Document(
                    page_content=data['sentence'],
                    metadata={"cause_effect": str(data['cause-effect']), "source": self.file_path},
                )

class CauseEffectWithTitleLoader(BaseLoader):
    '''非一般向方法，严禁调用'''
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        # 因为原始文件和输入的文件不是同一个，输入的是json格式，原始文件为docx格式，这里做了特殊处理
        self.file_title = os.path.basename(file_path).split('.')[0] + '.docx'
        self.encoding = get_encoding(self.file_path)

    def lazy_load(self) -> Iterator[Document]:
        with open(self.file_path, encoding=self.encoding) as f:
            datas = json.load(f)
            for data in datas:
                yield Document(
                    page_content=data['sentence'],
                    metadata={"cause_effect": str(data['cause-effect']), "source": self.file_path, "title": self.file_title},
                )
    async def alazy_load(
        self,
    ) -> AsyncIterator[Document]:
        import aiofiles

        async with aiofiles.open(self.file_path, encoding=self.encoding) as f:
            content = await f.read()
            async for data in json.loads(content):
                yield Document(
                    page_content=data['sentence'],
                    metadata={"cause_effect": str(data['cause-effect']), "source": self.file_path, "titile": self.file_title},
                )
                
class CausalGraphLoader(BaseLoader):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.encoding = get_encoding(self.file_path)

    def lazy_load(self) -> Iterator[Document]:
        with open(self.file_path, encoding=self.encoding) as f:
            datas = json.load(f)
            for data in datas:
                yield Document(
                    page_content=data['effect'],
                    metadata={"id": data['id'], "causes": str(data['cause'])},
                )
    async def alazy_load(
        self,
    ) -> AsyncIterator[Document]:
        import aiofiles

        async with aiofiles.open(self.file_path, encoding=self.encoding) as f:
            content = await f.read()
            async for data in json.loads(content):
                yield Document(
                    page_content=data['effect'],
                    metadata={"id": data['id'], "causes": str(data['cause'])},
                )