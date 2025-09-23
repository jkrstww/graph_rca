from fault_node import FaultNode
from typing import List

class ReasonPath:
    path = List[FaultNode]
    next = List[FaultNode]
    is_final = False

    def __init__(self, node: FaultNode):
        self.path.append(node)
        if node.next == []:
            self.is_final = True

    def add_node(self, node: FaultNode):
        self.path.append(node)
        self.next = node.next
        if node.next == []:
            self.is_final = True

    def explore(self):
        last_node = self.path[-1]

        if last_node.next == []:
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
        for node in self.path:
            ret += node.name
            ret += '<-'
        ret.rstrip('<-')

        return ret