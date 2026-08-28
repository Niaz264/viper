import time
from bot.helpers.utils import humanbytes
def make_progress_string(current, total, start_time):
    percent = round(current * 100 / total, 2) if total else 0
    speed = current / (time.time() - start_time) if time.time() - start_time > 0 else 0
    eta = round((total - current) / speed) if speed > 0 else 0

    filled_blocks = int(percent / 5)
    bar = '█' * filled_blocks + '░' * (20 - filled_blocks)

    eta_mins, eta_secs = divmod(eta, 60)
    eta_hrs, eta_mins = divmod(eta_mins, 60)
    eta_str = f"{int(eta_hrs)}h {int(eta_mins)}m {int(eta_secs)}s" if eta_hrs else f"{int(eta_mins)}m {int(eta_secs)}s"

    return f"[{bar}] {percent}%\nSpeed: {humanbytes(speed)}/s | ETA: {eta_str}\nDownloaded: {humanbytes(current)} of {humanbytes(total)}"
print(make_progress_string(5000000, 10000000, time.time() - 10))
