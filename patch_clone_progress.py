import re

with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Add getFolderSize method
size_method = """  def getFolderSize(self, folder_id):
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
"""
content = content.replace("  def cloneFolder(", size_method + "\n  def cloneFolder(")

# Update cloneFolder signature to take updater
content = content.replace(
    "def cloneFolder(self, name, local_path, folder_id, parent_id):",
    "def cloneFolder(self, name, local_path, folder_id, parent_id, updater=None, total_size=0):"
)
content = content.replace(
    "new_id = self.cloneFolder(file.get('name'), file_path, file.get('id'), current_dir_id)",
    "new_id = self.cloneFolder(file.get('name'), file_path, file.get('id'), current_dir_id, updater, total_size)"
)

# Update copyFile loop inside cloneFolder to call updater
updater_logic = """
            try:
                self.copyFile(file.get('id'), parent_id)
                if updater and total_size:
                    updater.update(self.transferred_size, total_size)
                new_id = parent_id
"""
content = content.replace("""            try:
                self.copyFile(file.get('id'), parent_id)
                new_id = parent_id""", updater_logic)

# Update clone to calculate size, init updater, and pass to cloneFolder
clone_logic = """  def clone(self, link, message=None):
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
        updater = ProgressUpdater(message, f"🗂️ **Cloning Folder...**\\n**Name:** `{meta.get('name')}`") if message else None
        dir_id = self.create_directory(meta.get('name'))
        result = self.cloneFolder(meta.get('name'), meta.get('name'), meta.get('id'), dir_id, updater, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(meta.get('name'), self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id), humanbytes(self.transferred_size))
      else:
        total_size = int(meta.get('size', 0))
        updater = ProgressUpdater(message, f"🗂️ **Cloning File...**\\n**Name:** `{meta.get('name')}`") if message else None
        file = self.copyFile(meta.get('id'), self.__parent_id)
        self.transferred_size += total_size
        if updater:
            updater.update(self.transferred_size, total_size)
        return Messages.COPIED_SUCCESSFULLY.format(file.get('name'), self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get('id')), humanbytes(total_size))
"""
content = re.sub(
    r'  def clone\(self, link\):.*?(?=  @retry\(wait=wait_exponential)',
    clone_logic,
    content,
    flags=re.DOTALL
)

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
