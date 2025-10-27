from pydantic import BaseModel
from typing import List

# 定义一条对话消息，包括对话角色，对话内容，对话时间
class ChatMessage(BaseModel):
    datetime: str
    content: str
    role: str

# 定义一个完整的对话历史
class ChatHistory(BaseModel):
    id: str
    create_time: str
    name: str
    messages: List[ChatMessage]

# 定义一个完整的根因分析历史
class AnalyseHistory(BaseModel):
    id: str
    created_time: str
    name: str
    reason_paths: List[str]
    summary: str

# 定义一个历史元数据
class History(BaseModel):
    id: str
    created_time: str
    name: str

# 定义每一个用户的历史记录
class UserHistory(BaseModel):
    user_id: str
    chat_history: List[History]
    analyse_history: List[History]