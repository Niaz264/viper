with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

# Fix getFolderSize (remove updater injection)
content = content.replace("""      from bot.helpers.utils import ProgressUpdater
      updater = ProgressUpdater(message, f'📥 **Downloading Folder...**\\n**Name:** `{os.path.basename(local_path)}`') if message else None
      for file in files:""", "      for file in files:")

# Fix cloneFolder (remove updater injection, it's passed as an argument!)
content = content.replace("""      from bot.helpers.utils import ProgressUpdater
      updater = ProgressUpdater(message, f'📥 **Downloading Folder...**\\n**Name:** `{os.path.basename(local_path)}`') if message else None
      for file in files:""", "      for file in files:")

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
