from pyrogram import Client, filters
from bot.config import BotCommands, Messages
from bot.helpers.utils import CustomFilters, humanbytes, TaskCancelledError
from bot.helpers.gdrive_utils import GoogleDrive
from bot import LOGGER

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Count) & CustomFilters.auth_users)
def _count(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        link = message.command[1]
        LOGGER.info(f'Count:{user_id}: {link}')
        sent_message = message.reply_text("🕵️ **Counting files and calculating size...**\n__You can reply to this message with /cancel to stop.__", quote=True)
        gdrive = GoogleDrive(user_id)

        try:
            folder_id = gdrive.getIdFromUrl(link)
        except Exception:
            sent_message.edit(Messages.INVALID_GDRIVE_URL)
            return

        try:
            # countFolder recursively computes folder stats.
            total_size, file_count, folder_count = gdrive.countFolder(folder_id, message=sent_message)

            result_str = (
                f"📊 **Count Results:**\n\n"
                f"📁 **Total Folders:** `{folder_count}`\n"
                f"📄 **Total Files:** `{file_count}`\n"
                f"💾 **Total Size:** `{humanbytes(total_size)}`"
            )
            sent_message.edit(result_str)
        except TaskCancelledError:
            sent_message.edit("❗ **Task Cancelled**")
        except Exception as e:
            sent_message.edit(f"**ERROR:** ```{str(e)}```")
    else:
        message.reply_text(f"**❗ Provide a valid Google Drive URL along with commmand.**\n__Usage - /{BotCommands.Count[0]} (GDrive Link)__", quote=True)
