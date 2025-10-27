import datetime

def getCurrentTime(self) -> str:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_time