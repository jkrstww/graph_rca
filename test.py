import json
from utils.file_utils import get_encoding
from typing import List


def transform_cause_effect(data):
    # # 创建一个字典来存储每个effect对应的cause列表
    # effect_to_causes = {}
    #
    # # 遍历原始数据
    # for item in data:
    #     cause_effect_pairs = item["cause_effect"]
    #
    #     # 处理每个cause-effect对
    #     for pair in cause_effect_pairs:
    #         # 分割cause和effect
    #         parts = pair.split(",")
    #         if len(parts) >= 2:
    #             cause = parts[0].strip()
    #             effect = parts[1].strip()
    #
    #             # 对每个effect，将当前cause添加到对应的列表中
    #             if effect not in effect_to_causes:
    #                 effect_to_causes[effect] = []
    #             effect_to_causes[effect].append(cause)
    #
    # # 构建新的数据结构
    # result = []
    # for idx, (effect, causes) in enumerate(effect_to_causes.items(), 1):
    #     result.append({
    #         "id": idx,
    #         "effect": effect,
    #         "cause": causes
    #     })
    #
    # return result
    # 使用字典来跟踪每个effect及其对应的cause列表
    effect_dict = {}
    id_counter = 1

    for input_data in data:
        # 处理cause_effect列表
        for pair in input_data["cause_effect"]:
            # 使用逗号分割字符串，获取cause和effect
            parts = pair.split(',', 1)  # 只分割第一个逗号，防止内容中有逗号
            if len(parts) == 2:
                cause_str = parts[0].strip()
                effect_str = parts[1].strip()

                # 如果effect已经存在，将cause添加到现有列表中
                if effect_str in effect_dict:
                    effect_dict[effect_str]["cause"].append(cause_str)
                else:
                    # 创建新对象
                    effect_dict[effect_str] = {
                        "id": id_counter,
                        "effect": effect_str,
                        "cause": [cause_str]
                    }
                    id_counter += 1
            else:
                # 如果分割失败，跳过并打印警告
                print(f"警告: 无效的因果关系对 '{pair}'，已跳过")

    # 将字典转换为列表
    output_list = list(effect_dict.values())
    return output_list


# file_path = './graph/transformer2.json'
# # 示例数据
# with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
#     input_data = json.load(f)
# f.close()
#
# # 执行转换
# output_data = transform_cause_effect(input_data)
#
# print(output_data)
# with open('./graph/graph.json', 'w', encoding='utf-8') as f:
#     json.dump(output_data, f, ensure_ascii=False, indent=4)
# f.close()

# from pydantic import BaseModel
# class ChatMessage(BaseModel):
#     datetime: str
#     content: str
#     role: str

# class ChatHistory(BaseModel):
#     id: str
#     create_time: str
#     name: str
#     messages: List[ChatMessage]

# messages = ChatMessage(datetime='111',content='222',role='333')
# history = ChatHistory(
#     id='',
#     create_time='',
#     name='',
#     messages=[]
# )
# history.messages.append(messages)

# print(history.model_dump_json(indent=2, exclude_none=True))

def qwen_api():
    from config import QWEN_KEY
    import os
    from openai import OpenAI

    client = OpenAI(
        api_key=QWEN_KEY,  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 百炼服务的base_url
    )

    completion = client.embeddings.create(
        model="text-embedding-v4",
        input='衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买',
        dimensions=1024, # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
        encoding_format="float"
    )

    print(completion.model_dump_json())


def format_jsonl_file(input_file, output_file, indent=2):
    """
    格式化JSONL文件，增加可读性
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        indent: 缩进空格数
    """
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if line:  # 跳过空行
                    try:
                        # 解析JSON
                        data = json.loads(line)
                        # 格式化输出
                        formatted_json = json.dumps(data, indent=indent, ensure_ascii=False)
                        f_out.write(formatted_json + '\n\n')  # 添加空行分隔
                    except json.JSONDecodeError as e:
                        print(f"第{line_num}行JSON解析错误: {e}")

# 使用示例
format_jsonl_file('./pairwise_causality.jsonl', 'pairwise_causality.json', indent=2)