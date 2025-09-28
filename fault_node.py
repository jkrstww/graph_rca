from typing import Optional,List

class FaultNode:
    def __init__(self, name: str, next_nodes: Optional[List['FaultNode']] = None):
        self.name = name
        self.next = next_nodes if next_nodes is not None else []

    def add_next(self, node: 'FaultNode'):
        if node not in self.next:
            self.next.append(node)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name