from fault_node import FaultNode
from typing import List, Optional

class ReasonPath:
    def __init__(self, node: Optional[FaultNode] = None, reason_path: Optional[List[FaultNode]] = None):
        self.path: List[FaultNode] = []
        self.is_final = False

        if node is not None and reason_path is not None:
            raise ValueError('要不输入头节点，要不输入完整的路径')

        if node is not None:
            self.path.append(node)

            if node.next == []:
                self.is_final = True
        elif reason_path is not None:
            for node in reason_path:
                self.path.append(node)

            if self.next() == []:
                self.is_final = True
        else:
            raise ValueError("没有参数输入，无法完成初始化")

    def add_node(self, node: FaultNode):
        self.path.append(node)

        if node.next == []:
            self.is_final = True
    
    def next(self):
        return self.path[-1].next

    def explore(self): 
        last_node = self.path[-1]

        if last_node.next == []:
            self.is_final = True
            return False
        else:
            while len(last_node.next) == 1:
                self.path.append(last_node)
                last_node = last_node.next[0]

            if last_node.next == []:
                self.is_final = True
                return False
            else:
                return True

    def __str__(self):
        ret = ''
        list_len = len(self.path)
        for i in range(list_len):
            node = self.path[i]
            ret += node.name
            if i != list_len - 1:
                ret += '<-'

        return ret
    
    def __repr__(self) -> str:
        ret = ''
        list_len = len(self.path)
        for i in range(list_len):
            node = self.path[i]
            ret += node.name
            if i != list_len - 1:
                ret += '<-'

        return ret

if __name__ == '__main__':
    list: List[FaultNode] = []
    node = FaultNode('test')
    node2 = FaultNode('test2')
    list.append(node)
    list.append(node2)

    reason_path = ReasonPath(reason_path=list)
    print(str(reason_path))