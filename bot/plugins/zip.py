import os
import shutil
from pyrogram import Client, filters
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages, BotCommands
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.gdrive_utils.gDrive import GoogleDrive

@Client.on_message(filters.incoming & filters.private & filters.command(BotCommands.Zip) & CustomFilters.auth_users)
def _zip(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        link = message.command[1]
        sent_message = message.reply_text(Messages.ZIP_DOWNLOADING.format(link), quote=True)
        gdrive = GoogleDrive(user_id)

        dl_path = os.path.join(DOWNLOAD_DIRECTORY, str(user_id))
        os.makedirs(dl_path, exist_ok=True)

        downloaded_path = gdrive.download(link, dl_path, sent_message)

        if downloaded_path and os.path.exists(downloaded_path):
            sent_message.edit(Messages.ZIPPING)
            zip_filename = f"{os.path.basename(downloaded_path)}"
            zip_filepath = os.path.join(DOWNLOAD_DIRECTORY, f"{zip_filename}.zip")

            if os.path.isdir(downloaded_path):
                shutil.make_archive(os.path.join(DOWNLOAD_DIRECTORY, zip_filename), 'zip', downloaded_path)
            else:
                tmp_dir = os.path.join(DOWNLOAD_DIRECTORY, f"tmp_{user_id}")
                os.makedirs(tmp_dir, exist_ok=True)
                shutil.move(downloaded_path, os.path.join(tmp_dir, os.path.basename(downloaded_path)))
                shutil.make_archive(os.path.join(DOWNLOAD_DIRECTORY, zip_filename), 'zip', tmp_dir)
                shutil.rmtree(tmp_dir)

            sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(f"{zip_filename}.zip", humanbytes(os.path.getsize(zip_filepath))))
            msg = gdrive.upload_file(zip_filepath, mimeType="application/zip", message=sent_message)
            sent_message.edit(msg)

            os.remove(zip_filepath)
            if os.path.isdir(downloaded_path):
                shutil.rmtree(downloaded_path)
            else:
                if os.path.exists(downloaded_path):
                    os.remove(downloaded_path)
        else:
            sent_message.edit(Messages.WENT_WRONG)
    else:
        message.reply_text(Messages.PROVIDE_GDRIVE_URL.format(BotCommands.Zip[0]), quote=True)


@Client.on_message(filters.incoming & filters.private & filters.command(BotCommands.Unzip) & CustomFilters.auth_users)
def _unzip(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        link = message.command[1]
        sent_message = message.reply_text(Messages.UNZIP_DOWNLOADING.format(link), quote=True)
        gdrive = GoogleDrive(user_id)

        dl_path = os.path.join(DOWNLOAD_DIRECTORY, str(user_id))
        os.makedirs(dl_path, exist_ok=True)

        downloaded_path = gdrive.download(link, dl_path, sent_message)

        if downloaded_path and os.path.exists(downloaded_path) and downloaded_path.endswith('.zip'):
            sent_message.edit(Messages.UNZIPPING)
            extract_dir = os.path.join(DOWNLOAD_DIRECTORY, f"extract_{user_id}")
            os.makedirs(extract_dir, exist_ok=True)

            try:
                shutil.unpack_archive(downloaded_path, extract_dir)

                # We need to upload this folder to GDrive
                folder_name = os.path.splitext(os.path.basename(downloaded_path))[0]
                dir_id = gdrive.create_directory(folder_name)

                # Clone the local folder to gdrive (similar to cloneFolder but from local)
                # Let's upload all files from extract_dir to dir_id

                # Calculate total size of the extracted folder
                total_size = 0
                for dirpath, _, filenames in os.walk(extract_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)

                from bot.helpers.utils import ProgressUpdater
                updater = ProgressUpdater(sent_message, f"📤 **Uploading Folder...**\n**Name:** `{folder_name}`")
                transferred_size_list = [0]

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

                def upload_local_folder(local_folder, parent_id):
                    for item in os.listdir(local_folder):
                        item_path = os.path.join(local_folder, item)
                        if os.path.isdir(item_path):
                            new_dir_id = gdrive.create_directory(item, parent_id=parent_id)
                            upload_local_folder(item_path, new_dir_id)
                        else:
                            file_updater = ProxyUpdater(updater, transferred_size_list, total_size)
                            gdrive.upload_file(item_path, parent_id=parent_id, updater=file_updater)

                upload_local_folder(extract_dir, dir_id)
                sent_message.edit(Messages.UPLOADED_SUCCESSFULLY.format(folder_name, gdrive._GoogleDrive__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id), humanbytes(total_size)))

            except Exception as e:
                LOGGER.error(e)
                sent_message.edit(Messages.UPLOAD_ERROR.format(str(e)))

            os.remove(downloaded_path)
            shutil.rmtree(extract_dir)
        else:
            if downloaded_path and os.path.exists(downloaded_path):
                if os.path.isdir(downloaded_path):
                    shutil.rmtree(downloaded_path)
                else:
                    os.remove(downloaded_path)
            sent_message.edit("❗ **Provided link is not a zip file or download failed.**")
    else:
        message.reply_text(Messages.PROVIDE_GDRIVE_URL.format(BotCommands.Unzip[0]), quote=True)
