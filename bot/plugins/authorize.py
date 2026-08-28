import re
import json
from httplib2 import Http
from bot import LOGGER, G_DRIVE_CLIENT_ID, G_DRIVE_CLIENT_SECRET
from bot.config import Messages
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bot.helpers.sql_helper import gDriveDB
from bot.config import BotCommands
from bot.helpers.utils import CustomFilters


OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
REDIRECT_URI = "http://localhost/"

flow = None

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Authorize))
async def _auth(client, message):
  user_id = message.from_user.id
  creds = gDriveDB.search(user_id)
  if creds is not None:
    creds.refresh(Http())
    gDriveDB._set(user_id, creds)
    await message.reply_text(Messages.ALREADY_AUTH, quote=True)
  else:
    global flow
    try:
      flow = OAuth2WebServerFlow(
              G_DRIVE_CLIENT_ID,
              G_DRIVE_CLIENT_SECRET,
              OAUTH_SCOPE,
              redirect_uri=REDIRECT_URI,
              response_type='code',
              access_type='offline',
              prompt='consent'
      )
      auth_url = flow.step1_get_authorize_url()
      LOGGER.info(f'AuthURL:{user_id}')
      await message.reply_text(
        text=Messages.AUTH_TEXT.format(auth_url),
        quote=True,
        reply_markup=InlineKeyboardMarkup(
                  [[InlineKeyboardButton("Authorization URL", url=auth_url)]]
              )
        )
    except Exception as e:
      await message.reply_text(f"**ERROR:** ```{e}```", quote=True)

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Revoke) & CustomFilters.auth_users)
def _revoke(client, message):
  user_id = message.from_user.id
  try:
    gDriveDB._clear(user_id)
    LOGGER.info(f'Revoked:{user_id}')
    message.reply_text(Messages.REVOKED, quote=True)
  except Exception as e:
    message.reply_text(f"**ERROR:** ```{e}```", quote=True)


@Client.on_message(filters.private & filters.incoming & filters.text & ~CustomFilters.auth_users)
async def _token(client, message):
  if "code=" in message.text:
    match = re.search(r"code=([^&\s]+)", message.text)
    if match:
      code = match.group(1)
    else:
      code = message.text.strip()
  else:
    code = message.text.strip()

  # Google OAuth2 authorization codes for native/loopback usually start with '4/' and have a specific length
  # Typically around 73 chars for standard codes, but sometimes around 32-35 chars depending on the format.
  # But we can at least check if it starts with '4/' or is reasonably long and doesn't contain spaces.
  if code and (code.startswith("4/") or (len(code) > 20 and " " not in code)):
    creds = None
    global flow
    if flow:
      try:
        user_id = message.from_user.id
        sent_message = await message.reply_text("🕵️**Checking received code...**", quote=True)
        creds = flow.step2_exchange(code)
        gDriveDB._set(user_id, creds)
        LOGGER.info(f'AuthSuccess: {user_id}')
        await sent_message.edit(Messages.AUTH_SUCCESSFULLY)
        flow = None
      except FlowExchangeError:
        await sent_message.edit(Messages.INVALID_AUTH_CODE)
      except Exception as e:
        await sent_message.edit(f"**ERROR:** ```{e}```")
    else:
        await sent_message.edit(Messages.FLOW_IS_NONE, quote=True)
