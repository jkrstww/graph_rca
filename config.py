# 在项目根目录的 config.py 或 __init__.py 中
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REFERENCE_PATH = os.path.join(PROJECT_ROOT, 'static', 'references')

QWEN_KEY = os.getenv('QWEN_KEY')