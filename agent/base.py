from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseAgent(ABC):
    system_instruction = ''

    def __init__(self):
        pass
