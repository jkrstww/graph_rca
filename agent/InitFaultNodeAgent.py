from agent.GenerateAgent import GenerateAgent
from typing import List, Set
from vectorbase.Chroma_method import ChromaVectorBase

class InitFaultNodeAgent(GenerateAgent):
    def __init__(self):
        super().__init__()

    def generate(self, input: str) -> str:
        return ''

    def output(self, fault_events: List[str]) -> Set[str]:
        # 引入数据库
        db = ChromaVectorBase()
        db.open('../vectorbase/dbs/Chroma/transformers')
        vector_store = db.vector_store()

        nodes = set()
        for event in fault_events:
            result = vector_store.similarity_search(
                event,
                k=1,
            )

            nodes.add(result)

        return nodes

