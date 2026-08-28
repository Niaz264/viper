import re

with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Modify download_file to take updater
content = content.replace(
    "def download_file(self, file_id, file_path):",
    "def download_file(self, file_id, file_path, updater=None):"
)
content = content.replace("""              status, done = downloader.next_chunk()
      return file_path""", """              status, done = downloader.next_chunk()
              if status and updater:
                  updater.update(status.resumable_progress, status.total_size)
      return file_path""")

# Modify downloadFolder to take message
content = content.replace(
    "def downloadFolder(self, folder_id, local_path):",
    "def downloadFolder(self, folder_id, local_path, message=None):"
)
content = content.replace(
    "self.downloadFolder(file.get('id'), file_path)",
    "self.downloadFolder(file.get('id'), file_path, message)"
)
content = content.replace(
    "self.download_file(file.get('id'), file_path)",
    "self.download_file(file.get('id'), file_path, updater)"
)
content = content.replace(
    "for file in files:",
    "from bot.helpers.utils import ProgressUpdater\n      updater = ProgressUpdater(message, f'📥 **Downloading Folder...**\\n**Name:** `{os.path.basename(local_path)}`') if message else None\n      for file in files:"
)

# Modify download to take message
content = content.replace(
    "def download(self, link, local_path):",
    "def download(self, link, local_path, message=None):"
)
content = content.replace(
    "return self.downloadFolder(meta.get('id'), path)",
    "return self.downloadFolder(meta.get('id'), path, message)"
)
content = content.replace(
    "return self.download_file(meta.get('id'), path)",
    "from bot.helpers.utils import ProgressUpdater\n              updater = ProgressUpdater(message, f'📥 **Downloading File...**\\n**Name:** `{meta.get(\\'name\\')}`') if message else None\n              return self.download_file(meta.get('id'), path, updater)"
)

# Modify upload_file
old_upload = """        uploaded_file = self.__service.files().create(body=body, media_body=media_body, fields='id', supportsTeamDrives=True).execute()
        file_id = uploaded_file.get('id')"""
new_upload = """        from bot.helpers.utils import ProgressUpdater
        updater = ProgressUpdater(message, f"📤 **Uploading File...**\\n**Filename:** `{filename}`\\n**Size:** `{filesize}`") if message else None
        request = self.__service.files().create(body=body, media_body=media_body, fields='id', supportsTeamDrives=True)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status and updater:
                updater.update(status.resumable_progress, status.total_size)
        file_id = response.get('id')"""
content = content.replace(old_upload, new_upload)
content = content.replace(
    "def upload_file(self, file_path, mimeType=None, parent_id=None):",
    "def upload_file(self, file_path, mimeType=None, parent_id=None, message=None):"
)

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
