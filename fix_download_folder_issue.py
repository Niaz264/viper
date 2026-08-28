with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Fix downloadFolder (remove updater injection)
content = content.replace("""      files = self.getFilesByFolderId(folder_id)
      for file in files:
          file_path = os.path.join(local_path, file.get('name'))
          if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
              self.downloadFolder(file.get('id'), file_path, message)
          else:
              self.download_file(file.get('id'), file_path, updater)""", """      files = self.getFilesByFolderId(folder_id)
      from bot.helpers.utils import ProgressUpdater
      updater = ProgressUpdater(message, f"📥 **Downloading Folder...**\\n**Name:** `{os.path.basename(local_path)}`") if message else None
      for file in files:
          file_path = os.path.join(local_path, file.get('name'))
          if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
              self.downloadFolder(file.get('id'), file_path, message)
          else:
              self.download_file(file.get('id'), file_path, updater)""")


with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
