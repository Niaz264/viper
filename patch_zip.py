import re

with open('bot/plugins/zip.py', 'r') as f:
    content = f.read()

# Pass message to download
content = content.replace(
    "downloaded_path = gdrive.download(link, dl_path)",
    "downloaded_path = gdrive.download(link, dl_path, sent_message)"
)

# Pass message to upload_file in _zip
content = content.replace(
    "msg = gdrive.upload_file(zip_filepath, mimeType=\"application/zip\")",
    "msg = gdrive.upload_file(zip_filepath, mimeType=\"application/zip\", message=sent_message)"
)

# Pass message to upload_file in upload_local_folder in _unzip
content = content.replace(
    "gdrive.upload_file(item_path, parent_id=parent_id)",
    "gdrive.upload_file(item_path, parent_id=parent_id, message=sent_message)"
)

with open('bot/plugins/zip.py', 'w') as f:
    f.write(content)
