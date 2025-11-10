from agent.base import BaseAgent
from langchain_ollama import ChatOllama
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from typing import List
import json
from vectorbase import ChromaVectorBase
from langchain_core.documents import Document
from config import PROJECT_ROOT
import uuid
import datetime
import os
import aiofiles

from history import ChatMessage, ChatHistory, UserHistory, History

from utils.file_utils import read_document_content
from utils.time_utils import getCurrentTime

from config import QWEN_KEY
os.environ["DASHSCOPE_API_KEY"] = QWEN_KEY


class ChatAgent(BaseAgent):
    history_path = PROJECT_ROOT + '/history/chats'

    def __init__(self):
        super().__init__()
        # 消息列表
        self.messages: List[BaseMessage] = []
        # 当前页面的历史记录
        self.history: ChatHistory = ChatHistory(
            id='',
            create_time='',
            name='',
            messages=[]
        )
        # 参考文献列表
        self.reference_list = []
        self.reference_list_latest = []
        self.model = ChatTongyi(
            model_name="qwen-plus",
            streaming=True
        )
        self.system_instruction = SystemMessage(
            content='''
                你是故障诊断领域的专家，你需要根据用户输入以及参考文献一步一步地对故障根本原因进行推理，
                在必要时，你需要询问用户，用于下一步的推理。
        ''')
        self.messages.append(self.system_instruction)
        # 对话的id，这个是前端那边要求的，虽然不知道有什么用
        self.chat_id = str(uuid.uuid4())

    def chat(self, query:str, user_id: str=''):
        initial_data = {
            "type": 'begin',
            "status": "starting!",
            "chat_id": self.chat_id
        }
        yield f"data: {json.dumps(initial_data)}\n\n"
        print("begin")
    
        # 加入模型对话框
        self.messages.append(HumanMessage(content=query))
        # 加入历史对话
        # 如果没有就新建
        if len(self.history.messages) == 0:
            self.history.create_time = getCurrentTime()
            # 以query前10个词作为名字
            self.history.name = query[:10]
            self.history.id = str(uuid.uuid4())

            # 建立用户和历史对话记录的联系
            # 查看有没有这个用户的记录
            file_name = user_id + '.json'
            file_path = PROJECT_ROOT + '/history/users/' + file_name
            user_list = os.listdir(PROJECT_ROOT + '/history/users')

            if file_name not in user_list:
                user_history = UserHistory(user_id=user_id, chat_history=[], analyse_history=[])
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                user_history = UserHistory.model_validate(data)
            
            # 新建一个History对象
            user_history.chat_history.append(
                History(
                    id=self.history.id, 
                    created_time=self.history.create_time, 
                    name=self.history.name
                ))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(user_history.model_dump_json(indent=2, exclude_none=True))
            f.close()

        self.history.messages.append(ChatMessage(datetime=getCurrentTime(), content=query, role='human'))

        # 查找参考文献并将其转化为提示词
        refs = self.generate_reference(query)
        def refsToPrompt(refs: List):
            content = '''
                以下是参考文献，其中:后面的是因果关系对，"A,B"代表A是因，B是果。
            '''
            for ref in refs:
                content += '[' + str(ref['id']) + ']' + ref['name'] + ':' + ref['cause_effect'] + ';'

            return content

        ref_prompt = refsToPrompt(refs)
        self.messages.append(HumanMessage(content=ref_prompt))

        # 流式生成回答
        full_text = ''
        for chunk in self.model.stream(self.messages):
            full_text += str(chunk.content)
            # yield json.dumps(chunk.content, ensure_ascii=False)
            chunk_data = {
                "type": "chunk",
                "content": chunk.content,
            }
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
        
        # 回答完成后加入到messages和历史记录中
        self.messages.append(AIMessage(content=full_text))
        self.history.messages.append(ChatMessage(datetime=getCurrentTime(), content=full_text, role='ai'))
        # 写入历史记录
        self.writeHistory()

        end_data = {
            "type": "end",
            "status": "completed",
        }
        yield f"data: {json.dumps(end_data)}\n\n"

    # 在完成每一轮对话后都会刷新历史记录状态,id唯一确认历史记录
    def writeHistory(self):
        file_name = self.history.id + '.json'

        file_path = PROJECT_ROOT + '/history/chats/' + file_name

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.history.model_dump_json(indent=2, exclude_none=True))
        f.close()
    
    # 读取历史记录
    def readHistory(self, id: str):
        '''读取历史记录'''
        # 要先清空当前的对话消息
        self.clear()
        file_path = PROJECT_ROOT + '/history/chats/' + id + '.json'

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    
        # 使用parse_raw方法解析JSON字符串
        self.history = ChatHistory.model_validate(data)

        # 在写入messages
        for message in self.history.messages:
            content = message.content
            if message.role == 'human':
                self.messages.append(HumanMessage(content))
            else:
                self.messages.append(AIMessage(content))
    
    def getHistoryList(self, user_id: str) -> List[dict[str, str]]:
        file_name = user_id + '.json'
        file_path = PROJECT_ROOT + '/history/users/' + file_name

        if os.path.exists(file_path) == False:
            return []
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            user_history = UserHistory.model_validate(data)

            list = user_history.chat_history
            return [
                {
                    'id': history.id,
                    'created_time': history.created_time,
                    'name': history.name
                } for history in list
            ]

    # 清理内存中的历史记录和对话记录以及参考文献，常用于重新开始一个对话
    def clear(self):
        self.clearMessages()

        self.history.id = ''
        self.history.name = ''
        self.history.create_time = ''
        self.history.messages = []

        self.clearReference()
    
    def new(self) -> str:
        '''重新开始一个对话'''
        self.clear()
        self.chat_id = str(uuid.uuid4())

        return self.chat_id

    def searchDB(self, prompt:str) -> List[Document]:
        db = ChromaVectorBase()
        db.open('transformers_with_title_qwen')
        vector_store = db.vector_store

        # retriever = vector_store.as_retriever(
        #     search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10}
        # )

        # result = retriever.invoke(prompt)

        result = vector_store.similarity_search(
            prompt,
            k=3,
        )

        return result
    
    # 根据用户查询生成参考文献
    def generate_reference(self, prompt: str):
        refs = self.searchDB(prompt)
        ret_list = []
        
        self.reference_list_latest.clear()

        for ref in refs:
            obj = ref.metadata
            name = obj['title']
            cause_effect = str(obj['cause_effect'])
            content = ref.page_content
            id = len(self.reference_list) + 1

            new_obj = {
                'id': id,
                'name': name,
                'cause_effect': cause_effect,
                'content': content
            }

            self.reference_list.append(new_obj)
            ret_list.append(new_obj)

            # 修改最新的参考文献列表
            self.reference_list_latest.append(new_obj)

        return ret_list
    
    def readReference(self, filename: str) -> str:
        file_path = PROJECT_ROOT + '/static/references' + '/' + filename

        content = read_document_content(file_path=file_path)

        return content

    
    def clearMessages(self):
        self.messages.clear()
        self.messages.append(self.system_instruction)
    
    def clearReference(self):
        while len(self.reference_list) != 0:
            self.reference_list.pop(0)