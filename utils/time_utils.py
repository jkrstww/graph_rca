from datetime import datetime

def getCurrentTime() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_time