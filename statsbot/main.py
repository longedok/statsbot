#!/usr/bin/env python3
import asyncio
import logging

from bot import Bot
from db import Database, QuestDbIngester, create_schema, db
from telegram_client import telegram_client
from service.stats_collector import StatsCollector

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting statsbot")

    questdb_ingester = QuestDbIngester()
    questdb_ingester.start()

    bot = Bot()
    stats_collector = StatsCollector(questdb_ingester)

    async def run():
        await db.connect()
        await create_schema()
        await asyncio.gather(bot.start(), stats_collector.start())

    with telegram_client:
        try:
            telegram_client.loop.run_until_complete(run())
        except KeyboardInterrupt:
            logger.info("Shutting down statsbot")
        finally:
            questdb_ingester.stop()
            telegram_client.loop.run_until_complete(db.disconnect())

    logger.info("Statsbot shut down")

if __name__ == "__main__":
    main()

