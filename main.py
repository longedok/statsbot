#!/usr/bin/env python3
import asyncio
import logging

from telethon.sync import TelegramClient

from bot import Bot
from settings import API_ID, API_HASH, SESSION_PATH
from service.stats_saver import QuestDbSaver
from service.stats_reporter import StatsReporter
from service.stats_collector import StatsCollector


logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting statsbot")

    telegram_client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    stats_saver = QuestDbSaver()
    stats_saver.start()

    bot = Bot(telegram_client, stats_saver)

    async def run():
        await bot.find_dialog()
        stats_reporter = StatsReporter(telegram_client, bot.channel_id)
        stats_collector = StatsCollector(stats_saver, stats_reporter)

        await asyncio.gather(bot.start(), stats_collector.start())

    with telegram_client:
        try:
            telegram_client.loop.run_until_complete(run())
        except KeyboardInterrupt:
            stats_saver.stop()
            stats_saver.join()

    logger.info("Shutting statsbot down")

if __name__ == "__main__":
    main()

