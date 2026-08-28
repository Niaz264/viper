import re

content = open('bot/helpers/gdrive_utils/gDrive.py').read()

new_upload = """  @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError), before=before_log(LOGGER, logging.DEBUG))
  def upload_file(self, file_path, mimeType=None, parent_id=None, message=None):
      mime_type = mimeType if mimeType else guess_type(file_path)[0]
      mime_type = mime_type if mime_type else "text/plain"
      media_body = MediaFileUpload(
          file_path,
          mimetype=mime_type,
          chunksize=150*1024*1024,
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
        from bot.helpers.utils import ProgressUpdater
        updater = ProgressUpdater(message, f"📤 **Uploading File...**\\n**Filename:** `{filename}`\\n**Size:** `{filesize}`")
        request = self.__service.files().create(body=body, media_body=media_body, fields='id', supportsTeamDrives=True)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status and updater:
                updater.update(status.resumable_progress, status.total_size)
        file_id = response.get('id')
        return Messages.UPLOADED_SUCCESSFULLY.format(filename, self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file_id), filesize)
      except HttpError as err:
        if err.resp.get('content-type', '').startswith('application/json'):
          reason = json.loads(err.content).get('error').get('errors')[0].get('reason')
          if reason == 'userRateLimitExceeded' or reason == 'dailyLimitExceeded':
            return Messages.RATE_LIMIT_EXCEEDED_MESSAGE
          else:
            return f"**ERROR:** {reason}"
      except Exception as e:
        return f"**ERROR:** ```{e}```"
"""
# Note: Google Drive API create() with resumable=True returns an HttpRequest that can be iterated with next_chunk()
