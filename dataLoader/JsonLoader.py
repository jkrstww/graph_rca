from typing import AsyncIterator, Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

import json

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
