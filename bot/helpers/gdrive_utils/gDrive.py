import os
import re
import json
import traceback
import logging
from bot import LOGGER
from time import sleep
from tenacity import *
import urllib.parse as urlparse
from bot.config import Messages
from mimetypes import guess_type
from urllib.parse import parse_qs
from bot.helpers.utils import humanbytes, CANCEL_TASKS, TaskCancelledError
import io
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from bot.helpers.sql_helper import gDriveDB, idsDB


logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
logging.getLogger('oauth2client.transport').setLevel(logging.ERROR)
logging.getLogger('oauth2client.client').setLevel(logging.ERROR)


class GoogleDrive:
  def __init__(self, user_id):
    self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
    self.__G_DRIVE_BASE_DOWNLOAD_URL = "https://drive.google.com/uc?id={}&export=download"
    self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = "https://drive.google.com/drive/folders/{}"
    self.__service = self.authorize(gDriveDB.search(user_id))
    self.__parent_id = idsDB.search_parent(user_id)

  def getIdFromUrl(self, link: str):
      try:
          parsed = urlparse.urlparse(link)
          if parsed.query:
              q = parse_qs(parsed.query)
              if 'id' in q:
                  return q['id'][0]
      except Exception:
          pass
      regex = r"(https?://)?(drive\.google\.com/)(drive)?/?u?/?\d?/?(mobile)?/?(file)?(folders)?/?d?/([-\w]+)[?+]?/?(w+)?"
      res = re.search(regex, link)
      if res:
          return res.group(7)
      raise IndexError("GDrive ID not found.")

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def getFilesByFolderId(self, folder_id):
      page_token = None
      q = f"'{folder_id}' in parents"
      files = []
      while True:
          response = self.__service.files().list(supportsTeamDrives=True,
                                                 includeTeamDriveItems=True,
                                                 q=q,
                                                 spaces='drive',
                                                 pageSize=200,
                                                 fields='nextPageToken, files(id, name, mimeType,size)',
                                                 pageToken=page_token).execute()
          for file in response.get('files', []):
              files.append(file)
          page_token = response.get('nextPageToken', None)
          if page_token is None:
              break
      return files


  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def copyFile(self, file_id, dest_id):
      body = {'parents': [dest_id]}
      try:
          res = self.__service.files().copy(supportsAllDrives=True,fileId=file_id,body=body).execute()
          return res
      except HttpError as err:
          if err.resp.get('content-type', '').startswith('application/json'):
              reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
              if reason == 'dailyLimitExceeded':
                 raise IndexError('LimitExceeded')
              else:
                 raise err


  def getFolderSize(self, folder_id):
      files = self.getFilesByFolderId(folder_id)
      total_size = 0
      for file in files:
          if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
              total_size += self.getFolderSize(file.get('id'))
          else:
              try:
                  total_size += int(file.get('size', 0))
              except ValueError:
                  pass
      return total_size

  def cloneFolder(self, name, local_path, folder_id, parent_id, updater=None, total_size=0):
      files = self.getFilesByFolderId(folder_id)
      new_id = None
      if len(files) == 0:
        return self.__parent_id
      for file in files:
        if updater and updater.message and CANCEL_TASKS.get(updater.message.id):
            raise TaskCancelledError("Task Cancelled")
        if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
            file_path = os.path.join(local_path, file.get('name'))
            current_dir_id = self.create_directory(file.get('name'))
            new_id = self.cloneFolder(file.get('name'), file_path, file.get('id'), current_dir_id, updater, total_size)
        else:
            try:
                self.transferred_size += int(file.get('size'))
            except TypeError:
                pass

            try:
                self.copyFile(file.get('id'), parent_id)
                if updater and total_size:
                    updater.update(self.transferred_size, total_size)
                new_id = parent_id

            except Exception as err:
                err_trace = traceback.format_exc()
                LOGGER.error(err_trace)
                return err_trace
      return new_id

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def create_directory(self, directory_name, parent_id=None):
          file_metadata = {
              "name": directory_name,
              "mimeType": self.__G_DRIVE_DIR_MIME_TYPE
          }
          target_parent = parent_id if parent_id else self.__parent_id
          file_metadata["parents"] = [target_parent]
          file = self.__service.files().create(supportsTeamDrives=True, body=file_metadata).execute()
          file_id = file.get("id")
          return file_id

  def clone(self, link, message=None):
    self.transferred_size = 0
    try:
      file_id = self.getIdFromUrl(link)
    except (IndexError, KeyError):
      return Messages.INVALID_GDRIVE_URL
    try:
      meta = self.__service.files().get(supportsAllDrives=True, fileId=file_id, fields="name,id,mimeType,size").execute()
      from bot.helpers.utils import ProgressUpdater
      if meta.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
        total_size = self.getFolderSize(meta.get('id'))
        updater = ProgressUpdater(message, f"🗂️ **Cloning Folder...**\n**Name:** `{meta.get('name')}`") if message else None
        dir_id = self.create_directory(meta.get('name'))
        result = self.cloneFolder(meta.get('name'), meta.get('name'), meta.get('id'), dir_id, updater, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(meta.get('name'), self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id), humanbytes(self.transferred_size))
      else:
        total_size = int(meta.get('size', 0))
        updater = ProgressUpdater(message, f"🗂️ **Cloning File...**\n**Name:** `{meta.get('name')}`") if message else None
        file = self.copyFile(meta.get('id'), self.__parent_id)
        self.transferred_size += total_size
        if updater:
            updater.update(self.transferred_size, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(file.get('name'), self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get('id')), humanbytes(total_size))
    except TaskCancelledError:
      return "❗ **Task Cancelled**"
    except Exception as err:
      if isinstance(err, RetryError):
        LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
        err = err.last_attempt.exception()
      err_str = str(err).replace(">", "").replace("<", "")
      err_trace = traceback.format_exc()
      LOGGER.error(err_trace)
      return f"**ERROR:** ```{err_trace}```"

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def upload_file(self, file_path, mimeType=None, parent_id=None, message=None, updater=None):
      mime_type = mimeType if mimeType else guess_type(file_path)[0]
      mime_type = mime_type if mime_type else "text/plain"
      media_body = MediaFileUpload(
          file_path,
          mimetype=mime_type,
          chunksize=5*1024*1024,
          resumable=True
      )
      filename = os.path.basename(file_path)
      filesize = humanbytes(os.path.getsize(file_path))
      body = {
          "name": filename,
          "description": "Uploaded using @UploadGdriveBot",
          "mimeType": mime_type,
      }
      target_parent = parent_id if parent_id else self.__parent_id
      body["parents"] = [target_parent]
      LOGGER.info(f'Upload: {file_path}')
      try:
        if not updater and message:
            from bot.helpers.utils import ProgressUpdater
            updater = ProgressUpdater(message, f"📤 **Uploading File...**\n**Filename:** `{filename}`\n**Size:** `{filesize}`")
        request = self.__service.files().create(body=body, media_body=media_body, fields='id', supportsTeamDrives=True)
        response = None
        while response is None:
            if updater and updater.message and CANCEL_TASKS.get(updater.message.id):
                raise TaskCancelledError("Task Cancelled")
            status, response = request.next_chunk()
            if status and updater:
                updater.update(status.resumable_progress, status.total_size)
        file_id = response.get('id')
        return Messages.UPLOADED_SUCCESSFULLY.format(filename, self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file_id), filesize)
      except TaskCancelledError:
        return "❗ **Task Cancelled**"
      except HttpError as err:
        if err.resp.get('content-type', '').startswith('application/json'):
          reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
          if reason == 'userRateLimitExceeded' or reason == 'dailyLimitExceeded':
            return Messages.RATE_LIMIT_EXCEEDED_MESSAGE
          else:
            return f"**ERROR:** {reason}"
      except Exception as e:
        return f"**ERROR:** ```{e}```"

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def checkFolderLink(self, link: str):
    try:
      file_id = self.getIdFromUrl(link)
    except (IndexError, KeyError):
      raise IndexError
    try:
      file = self.__service.files().get(supportsAllDrives=True, fileId=file_id, fields="mimeType").execute()
    except HttpError as err:
      if err.resp.get('content-type', '').startswith('application/json'):
        reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
        if 'notFound' in reason:
          return False, Messages.FILE_NOT_FOUND_MESSAGE.format(file_id)
        else:
          return False, f"**ERROR:** ```{str(err).replace('>', '').replace('<', '')}```"
    if str(file.get('mimeType')) == self.__G_DRIVE_DIR_MIME_TYPE:
      return True, file_id
    else:
      return False, Messages.NOT_FOLDER_LINK

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def download_file(self, file_id, file_path, updater=None):
      request = self.__service.files().get_media(fileId=file_id)
      with io.FileIO(file_path, 'wb') as fh:
          downloader = MediaIoBaseDownload(fh, request)
          done = False
          while done is False:
              if updater and getattr(updater, 'message', None) and CANCEL_TASKS.get(updater.message.id):
                  raise TaskCancelledError("Task Cancelled")
              elif updater and hasattr(updater, 'base_updater') and updater.base_updater.message and CANCEL_TASKS.get(updater.base_updater.message.id):
                  raise TaskCancelledError("Task Cancelled")
              status, done = downloader.next_chunk()
              if status and updater:
                  updater.update(status.resumable_progress, status.total_size)
      return file_path

  class ProxyUpdater:
      def __init__(self, base_updater, transferred_list, total_sz):
          self.base_updater = base_updater
          self.transferred_list = transferred_list
          self.total_size = total_sz
          self.current_file_progress = 0

      def update(self, current, total, *args, **kwargs):
          diff = current - self.current_file_progress
          self.current_file_progress = current
          self.transferred_list[0] += diff
          self.base_updater.update(self.transferred_list[0], self.total_size)

  def downloadFolder(self, folder_id, local_path, message=None, updater=None, total_size=None, transferred_size_list=None):
      if updater is None and message:
          from bot.helpers.utils import ProgressUpdater
          updater = ProgressUpdater(message, f"📥 **Downloading Folder...**\n**Name:** `{os.path.basename(local_path)}`")
          total_size = self.getFolderSize(folder_id)
          transferred_size_list = [0]

      os.makedirs(local_path, exist_ok=True)
      files = self.getFilesByFolderId(folder_id)
      for file in files:
          file_path = os.path.join(local_path, file.get('name'))
          if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
              self.downloadFolder(file.get('id'), file_path, message, updater, total_size, transferred_size_list)
          else:
              file_size = int(file.get('size', 0))
              if updater:
                  file_updater = self.ProxyUpdater(updater, transferred_size_list, total_size)
              else:
                  file_updater = None

              self.download_file(file.get('id'), file_path, file_updater)
      return local_path

  def download(self, link, local_path, message=None):
      try:
          file_id = self.getIdFromUrl(link)
      except (IndexError, KeyError):
          return Messages.INVALID_GDRIVE_URL
      try:
          meta = self.__service.files().get(supportsAllDrives=True, fileId=file_id, fields="name,id,mimeType,size").execute()
          path = os.path.join(local_path, meta.get('name'))
          if meta.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
              return self.downloadFolder(meta.get('id'), path, message)
          else:
              from bot.helpers.utils import ProgressUpdater
              updater = ProgressUpdater(message, f"📥 **Downloading File...**\n**Name:** `{meta.get('name')}`") if message else None
              return self.download_file(meta.get('id'), path, updater)
      except TaskCancelledError:
          if message:
              message.edit("❗ **Task Cancelled**")
          return None
      except RetryError as err:
          err = err.last_attempt.exception()
          err = str(err).replace('>', '').replace('<', '')
          LOGGER.error(err)
          return None
      except Exception as err:
          err = str(err).replace('>', '').replace('<', '')
          LOGGER.error(err)
          return None

  def countFolder(self, folder_id, message=None):
      files = self.getFilesByFolderId(folder_id)
      total_size = 0
      file_count = 0
      folder_count = 0
      for file in files:
          if message and CANCEL_TASKS.get(message.id):
              raise TaskCancelledError("Task Cancelled")
          if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
              folder_count += 1
              s, f, fd = self.countFolder(file.get('id'), message)
              total_size += s
              file_count += f
              folder_count += fd
          else:
              file_count += 1
              try:
                  total_size += int(file.get('size', 0))
              except ValueError:
                  pass
      return total_size, file_count, folder_count

  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def delete_file(self, link: str):
    try:
      file_id = self.getIdFromUrl(link)
    except (IndexError, KeyError):
      return Messages.INVALID_GDRIVE_URL
    try:
      self.__service.files().delete(fileId=file_id, supportsTeamDrives=True).execute()
      return Messages.DELETED_SUCCESSFULLY.format(file_id)
    except HttpError as err:
      if err.resp.get('content-type', '').startswith('application/json'):
        reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
        if 'notFound' in reason:
          return Messages.FILE_NOT_FOUND_MESSAGE.format(file_id)
        elif 'insufficientFilePermissions' in reason:
          return Messages.INSUFFICIENT_PERMISSONS.format(file_id)
        else:
          return f"**ERROR:** ```{str(err).replace('>', '').replace('<', '')}```"
      
  def emptyTrash(self):
    try:
      self.__service.files().emptyTrash().execute()
      return Messages.EMPTY_TRASH
    except HttpError as err:
      return f"**ERROR:** ```{str(err).replace('>', '').replace('<', '')}```"


  def authorize(self, creds):
    return build('drive', 'v3', credentials=creds, cache_discovery=False)