with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

content = content.replace('f"🗂️ **Cloning Folder...**\n**Name:**', 'f"🗂️ **Cloning Folder...**\\n**Name:**')
content = content.replace('f"🗂️ **Cloning File...**\n**Name:**', 'f"🗂️ **Cloning File...**\\n**Name:**')

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
