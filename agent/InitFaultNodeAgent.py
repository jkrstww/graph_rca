from agent.GenerateAgent import GenerateAgent
from typing import List, Set
from vectorbase.Chroma_method import ChromaVectorBase

class InitFaultNodeAgent(GenerateAgent):
    def __init__(self):
        super().__init__()

    def generate(self, input: str) -> str:
        return ''

    def output(self, fault_events: List[str]) -> List[str]:
        # 引入数据库
        db = ChromaVectorBase()
        db.open('graph')
        vector_store = db.vector_store

        nodes: List[str] = []
        for event in fault_events:
            result = vector_store.similarity_search(
                event,
                k=1,
            )

            node = result[0].page_content
            if node not in nodes:
                nodes.append(node)

        return nodes


if __name__ == '__main__':
    print('start testing!!!')
    input = ['变压器发热','绕组变形','放电','出现粉尘爆炸']

    agent = InitFaultNodeAgent()
    nodes = agent.output(fault_events=input)
    print(nodes)

