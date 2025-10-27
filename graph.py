from agent import *
from datetime import datetime, timedelta
from utils.file_utils import get_encoding
from utils.time_utils import getCurrentTime
import json
from typing import List, Dict
from fault_node import FaultNode
from reason_path import ReasonPath

from history import *

from typing import List, Optional
import uuid
import os

from config import PROJECT_ROOT

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
                self.graph[effect] = FaultNode(effect)

            node = self.graph[effect]

            for cause in causes:
                if cause not in self.graph:
                    self.graph[cause] = FaultNode(cause)

                node.next.append(self.graph[cause])

    def get_node(self, node: str) -> FaultNode:
        if node in self.graph:
            if node in self.graph:
                fault_node = self.graph.get(node)
                if type(fault_node) == FaultNode:
                    return fault_node
                else:
                    raise KeyError('没有找到节点' + node)
            else:
                return FaultNode('')
        else:
            return FaultNode(node)

class FaultAnalyseAgent():
    def __init__(self, session_id: str, user_id: str):
        self.fault_nodes: List[FaultNode] = []
        self.reason_paths: List[ReasonPath] = []
        self.graph = FaultGraph()
        self.id = session_id
        self.created_time = datetime.now()
        self.event_identify_agent = EventIdentifyAgent()
        self.init_fault_node_agent = InitFaultNodeAgent()
        self.generate_choice_agent = GenerateChoiceAgent()
        self.decide_next_agent = DecideNextAgent()
        self.final_summary_agent = FinalAnalyseAgent()
        self.chat_agent = ChatAgent()
        # self.graph.read_graph('./graph/graph.json')
        self.analyse_id = str(uuid.uuid4())
        self.final_summary = ''

    # def read_gragh(self, file_path: str):
    #     with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
    #         data = json.load(f)
    #     f.close()
    #     self.graph = data
    # 初始化，清空所有内容
    def clear(self):
        self.fault_nodes = []
        self.reason_paths = []
        self.final_summary = ''

    def new(self) -> str:
        '''重新开始根因分析'''
        self.clear()
        self.analyse_id = str(uuid.uuid4())

        return self.analyse_id
    
    def getHistory(self, user_id: str) -> List[str]:
        '''获取根因分析记录'''
        file_name = user_id + '.json'
        file_path = PROJECT_ROOT + '/history/users/' + file_name

        if os.path.exists(file_path) == False:
            return []
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            user_history = UserHistory.model_validate(data)

            list = user_history.analyse_history
            return [
                {
                    'id': history.id,
                    'created_time': history.created_time,
                    'name': history.name
                } for history in list
            ]

    def readHistory(self, id: str) -> AnalyseHistory:
        '''根据id读取根因分析历史记录'''
        file_path = PROJECT_ROOT + '/history/analyse/' + id + '.json'

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    
        # 使用parse_raw方法解析JSON字符串
        analyse_history = AnalyseHistory.model_validate(data)

        return analyse_history
    
    def writeHistory(self):
            '''在分析结束时写历史记录'''
            # 只有在结束时才生成历史记录
            history_id = str(uuid.uuid4())
            history = AnalyseHistory(
                id=history_id, 
                created_time=getCurrentTime(), 
                name=self.final_summary[:10],
                reason_paths=self.reason_paths,
                summary=self.final_summary)
            
            # 建立用户和历史对话记录的联系
            # 查看有没有这个用户的记录
            user_history_name = self.user_id + '.json'
            user_list = os.listdr(PROJECT_ROOT + '/history/users')

            user_history_path = PROJECT_ROOT + '/history/users/' + file_name

            if user_history_name not in user_list:
                user_history = UserHistory(user_id=self.user_id, chat_history=[], analyse_history=[])
            else:
                with open(user_history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                user_history = UserHistory.model_validate(data)
            
            # 更新用户历史记录映射表
            user_history.analyse_history.append(History(
                id=history.id,
                created_time=history.created_time,
                name=history.name
            ))

            with open(user_history_path, 'w', encoding='utf-8') as f:
                f.write(user_history.model_dump_json(indent=2, exclude_none=True))
            f.close()
            
            analyse_history_name = history_id + '.json'
            analyse_history_path = PROJECT_ROOT + '/history/analyse/' + analyse_history_name
            # 写入历史记录
            with open(analyse_history_path, 'w', encoding='utf-8') as f:
                f.write(history.model_dump_json(indent=2, exclude_none=True))
            f.close()

    # 根据当前的推理路径生成选项
    def generate_choice(self, reason_path: ReasonPath, candidate_nodes: List[FaultNode]) -> List[str]:
        try:
            choices = self.generate_choice_agent.output(reason_path=reason_path, candidate_nodes=candidate_nodes)

            return choices
        except Exception as e:
            raise e

    def perform_action(self, action_name, parameters):
        if action_name == 'generate_graph':
            # 每次生成图的时候都需要重置推理路径
            self.clear_path()
            print("start generate_graph")
            try:
                context = parameters['context']
                print('  -input:' + context)
                fault_events = self.event_identify_agent.output(context)
                print('  -identify_event:' + str(fault_events))
                fault_nodes_str = self.init_fault_node_agent.output(fault_events)
                print('  -fault_nodes:' + str(fault_nodes_str))

                # 初始化推理路径
                for node_str in fault_nodes_str:
                    node = self.graph.get_node(node_str)
                    
                    if node not in self.fault_nodes:
                        self.fault_nodes.append(node)
                        reason_path = ReasonPath(node)
                        # 根据初始节点尽可能往后面拓展，遇到分支或空节点终止
                        reason_path.explore()
                        self.reason_paths.append(reason_path)
                
                # 遍历path列表，找到一条没有结束的路径
                path_num = len(self.reason_paths)
                for i in range(path_num):
                    reason_path = self.reason_paths[0]

                    if reason_path.is_final:
                        old_path = self.reason_paths.pop()
                        self.reason_paths.append(old_path)
                    else:
                        choices = self.generate_choice(self.reason_paths[0], self.reason_paths[0].next())

                        return {
                            'is_final': False,
                            'reason_paths': [str(path) for path in self.reason_paths],
                            'choices': choices,
                            'analyse_id': self.analyse_id
                        }
                
                # 全部遍历一遍，发现都结束了
                self.final_summary = self.final_summary_agent.output(self.reason_paths)
                self.writeHistory()
                print("  -summary:"+self.final_summary)
                return {
                    "is_final": True,
                    "reason_paths": [str(path) for path in self.reason_paths],
                    "final_summary": self.final_summary,
                    'analyse_id': self.analyse_id
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
            print("start analyse")
            choices = parameters['choices']
            print("  -choices:"+str(choices))

            reason_path: ReasonPath = self.reason_paths[0]
            last_node: FaultNode = reason_path.path[-1]
            candidate_nodes = last_node.next

            print("    -current path:"+str(reason_path))
            print("    -cadidate nodes:"+str(candidate_nodes))

            update_fault_node_str = self.decide_next_agent.output(reason_path=reason_path, candidate_nodes=candidate_nodes, choices=choices)
            update_fault_node = self.graph.get_node(update_fault_node_str)
            reason_path.add_node(update_fault_node)
            print("    -new path:"+str(reason_path))
            print()

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
                    reason_path.explore()

                    if reason_path.is_final:
                        old_path = self.reason_paths.pop()
                        self.reason_paths.append(old_path)
                    else:
                        last_node: FaultNode = reason_path.path[-1]
                        candidate_nodes = last_node.next

                        choices = self.generate_choice_agent.output(reason_path, candidate_nodes)
                        return {
                            "is_final": False,
                            "reason_paths": [str(path) for path in self.reason_paths],
                            "choices": choices,
                            'analyse_id': self.analyse_id
                        }

            print('out')
            # 全部遍历一遍，发现都结束了
            self.final_summary = self.final_summary_agent.output(self.reason_paths)
            print("  -summary:"+self.final_summary)

            self.writeHistory()
            return {
                "is_final": True,
                "reason_paths": [str(path) for path in self.reason_paths],
                "final_summary": self.final_summary,
                'analyse_id': self.analyse_id
            }
        
        # 对话系统
        # elif action_name == 'chat':
        #     query = parameters['query']
        #     user_id = parameters['user_id']
        #     self.chat_agent.chat(query=query, user_id=user_id)
        # 根据history的id进行读取
        elif action_name == 'read_chat_history':
            id = parameters['history_id']
            self.chat_agent.readHistory(id)
            return self.chat_agent.history.model_dump_json()
        elif action_name == 'read_analyse_history':
            id = parameters['history_id']
            analyse_history = self.readHistory(id=id)
            return analyse_history.model_dump_json()
        elif action_name == 'get_chat_history':
            user_id = parameters['user_id']
            list = self.chat_agent.getHistoryList(user_id=user_id)
            return {
                "chat_history_list": list
            }
        elif action_name == 'get_analyse_history':
            user_id = parameters['user_id']
            list = self.getHistory(user_id=user_id)
            return {
                "analyse_history_list": list
            }
        elif action_name == 'new_chat':
            chat_id = self.chat_agent.new()
            return {
                "success": True,
                "message": "new chat connection!",
                "chat_id": chat_id
            }
        elif action_name == 'new_analyse':
            analyse_id = self.new()
            return {
                "success": True,
                "message": "new analyse connection!",
                "analyse_id": analyse_id
            }
        elif action_name == 'get_chat_ref':
            refs = self.chat_agent.reference_list()
            return {
                'chat_ref_list': [
                    {
                        'id': ref.id,
                        'name': ref.name,
                        'cause_effect': ref.cause_effect,
                        'content': ref.content
                    } for ref in refs
                ]
            }
        elif action_name == 'get_chat_ref_latest':
            refs = self.chat_agent.reference_list_latest()
            return {
                'chat_ref_list': [
                    {
                        'id': ref.id,
                        'name': ref.name,
                        'cause_effect': ref.cause_effect,
                        'content': ref.content
                    } for ref in refs
                ]
            }
        elif action_name == 'read_chat_ref':
            filename = parameters['filename']
            content = self.chat_agent.readReference(filename=filename)
            return {
                'content': content
            }
        

            

    def clear_path(self):
        self.reason_paths = []



if __name__ == '__main__':
    list: List[FaultNode] = []
    node = FaultNode('test')
    node2 = FaultNode('test2')
    list.append(node)
    list.append(node2)

    print(list)
