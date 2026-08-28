from pyrogram import Client, filters
from bot.config import BotCommands
from bot.helpers.utils import CustomFilters, CANCEL_TASKS

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Cancel) & CustomFilters.auth_users)
def _cancel(client, message):
    if message.reply_to_message:
        CANCEL_TASKS[message.reply_to_message.id] = True
        message.reply_text("✅ **Cancellation requested.**\n__The task will stop shortly if it is still running.__", quote=True)
    else:
        message.reply_text("❗ **Reply to the progress message of the task you want to cancel.**", quote=True)
