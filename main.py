#!/usr/bin/env python3
import logging
import asyncio

from telethon.sync import TelegramClient

from bot import Bot
from settings import API_ID, API_HASH, SESSION_PATH

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO,
)

telegram_client = TelegramClient(SESSION_PATH, API_ID, API_HASH) 


async def main():
    bot = Bot(telegram_client)

    await find_dialog(telegram_client, "бесстыжая")
    await asyncio.gather(bot.start())


async def find_dialog(telegram_client, title, limit=10):
    dialogs = await telegram_client.get_dialogs(limit=limit)
    for dialog in dialogs:
        if title in dialog.name.lower():
            return dialog


if __name__ == "__main__":
    with telegram_client:
        telegram_client.loop.run_until_complete(main())

