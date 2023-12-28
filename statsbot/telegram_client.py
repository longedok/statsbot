from telethon.sync import TelegramClient

from settings import API_ID, API_HASH, SESSION_PATH

telegram_client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

