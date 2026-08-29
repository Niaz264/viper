import os
import subprocess
import time
import re
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.helpers.utils import CANCEL_TASKS, TaskCancelledError

class Aria2Helper:
    def download(self, url, dl_path, updater=None):
        try:
            cmd = [
                "aria2c",
                "--console-log-level=notice",
                "--summary-interval=1",
                "-d", dl_path,
                url
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            downloaded_file = None

            for line in iter(process.stdout.readline, ""):
                if updater and updater.message and CANCEL_TASKS.get(updater.message.id):
                    process.terminate()
                    raise TaskCancelledError("Task Cancelled")

                # Check for file path
                if "Download complete:" in line:
                    downloaded_file = line.split("Download complete:")[1].strip()
                elif line.startswith("FILE:"):
                    downloaded_file = line.split("FILE:")[1].strip()

                # Check for progress
                # Format: [#2075fb 304KiB/10MiB(2%) CN:1 DL:612KiB ETA:16s]
                progress_match = re.search(r'\[#.*? \s*(.+?)/(.+?)\((.+?)%\)', line)
                if progress_match and updater:
                    try:
                        current_str, total_str, percent_str = progress_match.groups()

                        def parse_size(size_str):
                            size_str = size_str.replace('iB', 'B')
                            if size_str.endswith('B'):
                                val = float(size_str[:-2])
                                unit = size_str[-2:]
                                if unit == 'KB': return val * 1024
                                if unit == 'MB': return val * 1024 * 1024
                                if unit == 'GB': return val * 1024 * 1024 * 1024
                            return 0

                        current = parse_size(current_str)
                        total = parse_size(total_str)

                        updater.update(current, total)
                    except Exception as e:
                        pass

            process.wait()

            if process.returncode == 0:
                if not downloaded_file:
                    # Try to find it in dl_path if not found in output
                    filename = url.split('/')[-1]
                    potential_path = os.path.join(dl_path, filename)
                    if os.path.exists(potential_path):
                        downloaded_file = potential_path

                if downloaded_file and os.path.exists(downloaded_file):
                    return True, downloaded_file
                else:
                    return False, "Download completed but file not found."
            else:
                return False, f"aria2c failed with return code {process.returncode}"

        except TaskCancelledError:
            return False, "Task Cancelled"
        except Exception as e:
            return False, str(e)
