from agent import *
from datetime import datetime, timedelta
from utils.file_utils import get_encoding
import json
from typing import List, Dict
from fault_node import FaultNode
from reason_path import ReasonPath

from typing import List, Optional

class FaultGraph:
    graph: Dict[str, FaultNode] = {}

    def __init__(self):
        self.read_graph('./graph/graph.json')

    def read_graph(self, file_path: str):
        with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
            data = json.load(f)
        f.close()

        for item in data:
            effect = item['effect']
            causes = item['cause']

            if effect not in self.graph:
                node = FaultNode(effect)
            else:
                node = self.graph[effect]

            for cause in causes:
                if cause not in self.graph:
                    next = FaultNode(cause)
                    node.next.append(next)
                else:
                    node.next.append(self.graph[cause])

    def get_node(self, node: str):
        if node in self.graph:
            return self.graph.get(node)
        else:
            return FaultNode(node)

class FaultAnalyseAgent():
    graph = FaultGraph()
    fault_nodes = List[FaultNode]
    reason_paths = List[ReasonPath]
    def __init__(self, user_id: str):
        self.id = 'agent_' + user_id
        self.created_time = datetime.now()
        self.event_identify_agent = EventIdentifyAgent()
        self.init_fault_node_agent = InitFaultNodeAgent()
        self.generate_choice_agent = GenerateChoiceAgent()
        self.decide_next_agent = DecideNextAgent()
        self.final_summary_agent = FinalAnalyseAgent()
        self.graph.read_graph('./graph/graph.json')

    # def read_gragh(self, file_path: str):
    #     with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
    #         data = json.load(f)
    #     f.close()
    #     self.graph = data

    # 根据当前的推理路径生成选项
    def generate_choice(self, reason_path: ReasonPath, candidate_nodes: List[FaultNode]) -> List[str]:
        try:
            choices = self.generate_choice_agent.output(reason_path=reason_path, candidate_nodes=candidate_nodes)
            return choices
        except Exception as e:
            raise e

    def perform_action(self, action_name, parameters):
        if action_name == 'generate_graph':
            print("start generate_graph")
            try:
                context = parameters['context']
                print('  -input:' + context)
                fault_events = self.event_identify_agent.output(context)
                print('  -identify_event:' + str(fault_events))
                fault_nodes_str = self.init_fault_node_agent.output(fault_events)
                print('  -fault_nodes:' + fault_nodes_str)

                # 初始化推理路径
                for node_str in fault_nodes_str:
                    node = self.graph.get_node(node_str)
                    self.fault_nodes.append(node)
                    self.reason_paths.append(ReasonPath(node))

                return {
                    'reason_paths': str(self.reason_paths)
                }
            except Exception as e:
                return {
                    'error': e
                }

        # 根据当前的故障节点，以及图的结构先进行搜索，当搜索遇到分支时，选择生成选项
        # 搜索的逻辑：
        # 使用一个reason_path列表存储所有的推理路径，使用广度优先搜索算法对每一条路径进行搜索
        # 在对一条路径进行搜索时，按照有向边的方向进行搜索，遇到分支则触发选择生成支
        # 确定新加入的节点后将这条路径放在最后面
        # 路径走到尽头则不再进行处理
        elif action_name == 'root_cause_analyse':
            choices = parameters['choices']

            reason_path: ReasonPath = self.reason_paths[0]
            last_node: FaultNode = reason_path[-1]
            candidate_nodes = last_node.next

            update_fault_node_str = self.decide_next_agent.output(reason_path=reason_path, candidate_nodes=candidate_nodes, choices=choices)
            update_fault_node = self.graph.get_node(update_fault_node_str)
            reason_path.add_node(update_fault_node)

            # 把当前路径放在最后
            old_path = self.reason_paths.pop()
            self.reason_paths.append(old_path)

            # 遍历path列表，找到一条没有结束的路径
            path_num = len(self.reason_paths)
            for i in range(path_num):
                reason_path = self.reason_paths[0]

                if reason_path.is_final:
                    old_path = self.reason_paths.pop()
                    self.reason_paths.append(old_path)
                else:
                    choices: List[str] = []
                    while reason_path.explore():
                        last_node: FaultNode = reason_path[-1]
                        candidate_nodes = last_node.next

                        choices = self.generate_choice_agent.output(reason_path, candidate_nodes)
                        break

                    if reason_path.is_final:
                        old_path = self.reason_paths.pop()
                        self.reason_paths.append(old_path)
                    else:
                        return {
                            "is_final": False,
                            "reason_paths": str(self.reason_paths),
                            "choices": choices
                        }

            # 全部遍历一遍，发现都结束了
            final_summary = self.final_summary_agent(self.reason_paths)
            return {
                "is_final": True,
                "final_summary": final_summary
            }




if __name__ == '__main__':
    agent = FaultAnalyseAgent('test')
    print(agent.graph['graph'][0])
