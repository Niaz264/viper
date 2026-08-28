with open('bot/helpers/gdrive_utils/gDrive.py', 'r') as f:
    content = f.read()

content = content.replace("f'📥 **Downloading File...**\\n**Name:** `{meta.get(\\'name\\')}`'", 'f"📥 **Downloading File...**\\n**Name:** `{meta.get(\'name\')}`"')

with open('bot/helpers/gdrive_utils/gDrive.py', 'w') as f:
    f.write(content)
