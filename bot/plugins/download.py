import os
import shutil
from time import sleep
from pyrogram import Client, filters
from bot.helpers.qbit.qbit_helper import QbitHelper
from bot.helpers.sql_helper import gDriveDB, idsDB
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.downloader import download_file, utube_dl
from bot.helpers.gdrive_utils import GoogleDrive 
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages, BotCommands
from pyrogram.errors import FloodWait, RPCError

@Client.on_message(filters.private & filters.incoming & filters.text & (filters.command(BotCommands.Download) | filters.regex('^(ht|f)tp*')) & CustomFilters.auth_users)
def _download(client, message):
  user_id = message.from_user.id
  if not message.media:
    sent_message = message.reply_text('🕵️**Checking link...**', quote=True)
    if message.command:
      link = message.command[1]
    else:
      link = message.text
    if 'drive.google.com' in link:
      sent_message.edit(Messages.CLONING.format(link))
      LOGGER.info(f'Copy:{user_id}: {link}')
      msg = GoogleDrive(user_id).clone(link, sent_message)
      sent_message.edit(msg)
    else:
      if '|' in link:
        link, filename = link.split('|')
        link = link.strip()
        filename.strip()
        dl_path = os.path.join(f'{DOWNLOAD_DIRECTORY}/{filename}')
      else:
        link = link.strip()
        filename = os.path.basename(link)
        dl_path = DOWNLOAD_DIRECTORY
      LOGGER.info(f'Download:{user_id}: {link}')
      sent_message.edit(Messages.DOWNLOADING.format(link))
      result, file_path = download_file(link, dl_path, message=sent_message)
      if result == True:
        sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
        msg = GoogleDrive(user_id).upload_file(file_path, message=sent_message)
        sent_message.edit(msg)
        LOGGER.info(f'Deleteing: {file_path}')
        os.remove(file_path)
      elif file_path == "Task Cancelled":
        sent_message.edit("❗ **Task Cancelled**")
      else:
        sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))


@Client.on_message(filters.private & filters.incoming & (filters.document | filters.audio | filters.video | filters.photo) & CustomFilters.auth_users)
def _telegram_file(client, message):
  user_id = message.from_user.id
  sent_message = message.reply_text('🕵️**Checking File...**', quote=True)
  if message.document:
    file = message.document
  elif message.video:
    file = message.video
  elif message.audio:
    file = message.audio
  elif message.photo:
    file = message.photo
    file.mime_type = "images/png"
    file.file_name = f"IMG-{user_id}-{message.id}.png"
  sent_message.edit(Messages.DOWNLOAD_TG_FILE.format(file.file_name, humanbytes(file.file_size), file.mime_type))
  LOGGER.info(f'Download:{user_id}: {file.file_id}')
  try:
    from bot.helpers.utils import ProgressUpdater, TaskCancelledError
    updater = ProgressUpdater(sent_message, "📥 **Downloading Telegram File...**")
    file_path = message.download(file_name=DOWNLOAD_DIRECTORY, progress=updater.update)
    sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
    msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type, message=sent_message)
    sent_message.edit(msg)
  except TaskCancelledError:
    sent_message.edit("❗ **Task Cancelled**")
    if 'file_path' in locals() and file_path and os.path.exists(file_path):
        os.remove(file_path)
    return
  except RPCError:
    sent_message.edit(Messages.WENT_WRONG)
  if 'file_path' in locals() and file_path and os.path.exists(file_path):
      LOGGER.info(f'Deleteing: {file_path}')
      os.remove(file_path)

@Client.on_message(filters.incoming & filters.private & filters.command(BotCommands.YtDl) & CustomFilters.auth_users)
def _ytdl(client, message):
  user_id = message.from_user.id
  if len(message.command) > 1:
    sent_message = message.reply_text('🕵️**Checking Link...**', quote=True)
    link = message.command[1]
    LOGGER.info(f'YTDL:{user_id}: {link}')
    sent_message.edit(Messages.DOWNLOADING.format(link))
    from bot.helpers.utils import ProgressUpdater
    updater = ProgressUpdater(sent_message, "📥 **Downloading Video...**")
    result, file_path = utube_dl(link, updater)
    if result:
      sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
      msg = GoogleDrive(user_id).upload_file(file_path, message=sent_message)
      sent_message.edit(msg)
      LOGGER.info(f'Deleteing: {file_path}')
      os.remove(file_path)
    elif "Task Cancelled" in str(file_path):
      sent_message.edit("❗ **Task Cancelled**")
    else:
      sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))
  else:
    message.reply_text(Messages.PROVIDE_YTDL_LINK, quote=True)


@Client.on_message(filters.incoming & filters.private & filters.command(['qbit']) & CustomFilters.auth_users)
def _qbit(client, message):
  user_id = message.from_user.id
  if len(message.command) > 1:
    sent_message = message.reply_text('🕵️**Checking Link...**', quote=True)
    from bot.helpers.gdrive_utils import GoogleDrive
    from bot import LOGGER

    args = message.text.split()
    link = args[1]

    seed = "-seed" in args
    upload_drive = "-d" in args

    LOGGER.info(f'QBIT:{user_id}: {link} (Seed: {seed}, Drive: {upload_drive})')
    sent_message.edit(Messages.DOWNLOADING.format(link))

    from bot.helpers.utils import ProgressUpdater
    updater = ProgressUpdater(sent_message, "📥 **Downloading Torrent...**")

    qbit = QbitHelper()
    success, res = qbit.add_torrent(link)

    if success:
        result, file_path = qbit.wait_for_download(link, updater, seed)
        if result:
            is_dir = os.path.isdir(file_path)
            upload_path = file_path

            if is_dir:
                sent_message.edit("🗜️ **Zipping directory...**")
                # Zip the directory
                zip_path = file_path + ".zip"
                shutil.make_archive(file_path, 'zip', file_path)
                upload_path = zip_path

            sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(upload_path), humanbytes(os.path.getsize(upload_path))))

            if upload_drive:
                msg = GoogleDrive(user_id).upload_file(upload_path, message=sent_message)
                sent_message.edit(msg)
            else:
                try:
                    upload_updater = ProgressUpdater(sent_message, "📤 **Uploading to Telegram...**")
                    message.reply_document(document=upload_path, progress=upload_updater.update, quote=True)
                    sent_message.edit("✅ **Uploaded to Telegram Successfully.**")
                except Exception as e:
                    sent_message.edit(f"❗ **Upload to Telegram Failed:** `{e}`")

            if not seed:
                LOGGER.info(f'Deleting local files: {file_path}')
                if is_dir:
                    shutil.rmtree(file_path)
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                else:
                    os.remove(file_path)

                torrent = qbit.get_latest_torrent(link)
                if torrent:
                    qbit.delete_torrent(torrent.hash, delete_files=True)
            else:
                if is_dir and os.path.exists(zip_path):
                    os.remove(zip_path)

        elif "Task Cancelled" in str(file_path):
            sent_message.edit("❗ **Task Cancelled**")
        else:
            sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))
    else:
        sent_message.edit(Messages.DOWNLOAD_ERROR.format(res, link))
  else:
    message.reply_text("❗**Provide a valid magnet link or torrent url.**\nUsage: `/qbit <link> [-seed] [-d]`", quote=True)