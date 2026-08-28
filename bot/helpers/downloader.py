import os
import wget
import glob
import yt_dlp
import time
from pySmartDL import SmartDL
from urllib.error import HTTPError
from yt_dlp.utils import DownloadError
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.helpers.utils import CANCEL_TASKS, TaskCancelledError

def download_file(url, dl_path, message=None):
  try:
    dl = SmartDL(url, dl_path, progress_bar=False)
    LOGGER.info(f'Downloading: {url} in {dl_path}')
    dl.start(blocking=False)
    while not dl.isFinished():
        if message and CANCEL_TASKS.get(message.id):
            dl.stop()
            raise TaskCancelledError("Task Cancelled")
        time.sleep(1)
    if dl.isSuccessful():
        return True, dl.get_dest()
    else:
        return False, "Failed to download"
  except TaskCancelledError:
      return False, "Task Cancelled"
  except HTTPError as error:
    return False, error
  except Exception as error:
    try:
      def custom_bar(current, total, width=80):
          if message and CANCEL_TASKS.get(message.id):
              raise TaskCancelledError("Task Cancelled")

      filename = wget.download(url, dl_path, bar=custom_bar)
      return True, os.path.join(f"{DOWNLOAD_DIRECTORY}/{filename}")
    except TaskCancelledError:
      return False, "Task Cancelled"
    except HTTPError as err:
      return False, err


def utube_dl(link, updater=None):
  ytdl_opts = {
    'outtmpl' : os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
    'noplaylist' : True,
    'logger': LOGGER,
    'format': 'bestvideo+bestaudio/best',
    'geo_bypass_country': 'IN'
  }

  if updater:
      def progress_hook(d):
          if updater.message and CANCEL_TASKS.get(updater.message.id):
              raise TaskCancelledError("Task Cancelled")
          if d['status'] == 'downloading':
              current = d.get('downloaded_bytes', 0)
              total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
              if total > 0:
                  updater.update(current, total)
      ytdl_opts['progress_hooks'] = [progress_hook]

  with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
    try:
      meta = ytdl.extract_info(link, download=True)
      if 'requested_downloads' in meta and len(meta['requested_downloads']) > 0:
          path = meta['requested_downloads'][0].get('filepath')
      else:
          path = ytdl.prepare_filename(meta)

      if path and os.path.exists(path):
          return True, path
      return False, 'Something went wrong! No video file exists on server.'
    except DownloadError as e:
      return False, str(e)
    except Exception as e:
      return False, str(e)
