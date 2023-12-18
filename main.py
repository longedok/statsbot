#!/usr/bin/env python3
import logging
import asyncio

from telethon.sync import TelegramClient

from bot import Bot
from settings import API_ID, API_HASH

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO,
)


def main():
    telegram_client = TelegramClient('stats-bot', API_ID, API_HASH) 
    bot = Bot(telegram_client)

    with telegram_client:
        telegram_client.loop.run_until_complete(bot.start())


async def find_dialog(telegram_client, title, limit=10):
    dialogs = await telegram_client.get_dialogs(limit=limit)
    for dialog in dialogs:
        if title in dialog.name.lower():
            print(dialog)
            return dialog


if __name__ == "__main__":
    main()

