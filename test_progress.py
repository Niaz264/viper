import time
from bot.helpers.utils import humanbytes

def get_progress_bar(percentage):
    bar_length = 20
    filled_length = int(bar_length * percentage // 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    return bar

class ProgressUpdater:
    def __init__(self, message, action_text):
        self.message = message
        self.action_text = action_text
        self.start_time = time.time()
        self.last_update_time = 0

    def update(self, current, total):
        now = time.time()
        if now - self.last_update_time < 3 and current < total:
            return
        self.last_update_time = now

        percentage = current * 100 / total if total else 0
        speed = current / (now - self.start_time) if now - self.start_time > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        eta_mins, eta_secs = divmod(int(eta), 60)
        eta_hrs, eta_mins = divmod(eta_mins, 60)
        eta_str = f"{eta_hrs}h {eta_mins}m {eta_secs}s" if eta_hrs else f"{eta_mins}m {eta_secs}s"

        progress_str = (
            f"**{self.action_text}**\n"
            f"[{get_progress_bar(percentage)}] {percentage:.2f}%\n"
            f"**Speed**: {humanbytes(speed)}/s\n"
            f"**Done**: {humanbytes(current)} / {humanbytes(total)}\n"
            f"**ETA**: {eta_str}"
        )
        print(progress_str)

p = ProgressUpdater(None, "Downloading")
p.update(1000000, 10000000)
time.sleep(3.1)
p.update(5000000, 10000000)
