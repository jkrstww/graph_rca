import chardet
import re
import os

def get_encoding(file_path):
    """
    检测文件的编码格式，并正确处理文件路径

    参数:
        file_path: 文件路径，可以是绝对路径或相对路径

    返回:
        文件的编码格式
    """

    # 如果传入的是相对路径，尝试多种方式解析
    if not os.path.isabs(file_path):
        # 方法1: 基于当前工作目录
        abs_path_from_cwd = os.path.abspath(file_path)

        # 方法2: 基于调用者位置
        try:
            import inspect
            caller_frame = inspect.stack()[1]
            caller_file = caller_frame.filename
            caller_dir = os.path.dirname(os.path.abspath(caller_file))
            abs_path_from_caller = os.path.join(caller_dir, file_path)
        except (IndexError, AttributeError):
            abs_path_from_caller = None

        # 方法3: 基于当前脚本位置
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path_from_script = os.path.join(current_script_dir, file_path)

        # 尝试所有可能的路径，选择第一个存在的
        possible_paths = [
            abs_path_from_cwd,
            abs_path_from_caller,
            abs_path_from_script
        ]

        # 移除None值
        possible_paths = [p for p in possible_paths if p is not None]

        # 尝试每个路径
        for path in possible_paths:
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                file_path = normalized_path
                break
        else:
            # 如果没有找到任何存在的路径，使用基于当前工作目录的路径
            file_path = os.path.normpath(abs_path_from_cwd)

    # 规范化路径（处理 ../ 和 ./ 等）
    file_path = os.path.normpath(file_path)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not os.path.isfile(file_path):
        raise IsADirectoryError(f"路径指向的是目录而不是文件: {file_path}")

    with open(file_path, 'rb') as f:
        tmp = chardet.detect(f.read())
        return tmp['encoding']

def extract_label_content(text: str, label: str) -> list:
    """
    从文本中提取所有被<label></label>标签包含的内容

    Args:
        text: 要搜索的文本
        label: 标签名

    Returns:
        包含所有匹配内容的列表，如果没有找到则返回空列表
    """
    # 构建正则表达式模式，注意转义标签名
    pattern = f"<{label}>(.*?)</{label}>"

    # 使用非贪婪模式查找所有匹配项
    matches = re.findall(pattern, text, re.DOTALL)

    # 返回匹配结果列表
    return matches if matches else []

if __name__ == '__main__':
    sample_text = """
    <events>
    <event>变压器温度升高</event>
    <event>绝缘油泄漏</event>
    <event>保护装置动作</event>
    </events>
    还有一些其他文本<event>额外事件</event>
    """

    # 提取event标签内容
    events = extract_label_content(sample_text, "event")
    print(events)  # 输出: ['变压器温度升高', '绝缘油泄漏', '保护装置动作', '额外事件']

    # 提取不存在的标签内容
    none_results = extract_label_content(sample_text, "nonexistent")
    print(none_results)  # 输出: []