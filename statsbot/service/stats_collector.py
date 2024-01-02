import asyncio
import logging

from dao import chat_dao
from service.stats_service import stats_service

logger = logging.getLogger(__name__)


class StatsCollector:
    COLLECT_INTERVAL_SEC = 5 * 60

    def __init__(self, questdb_ingester):
        self.questdb_ingester = questdb_ingester

    async def start(self):
        logger.info("Enter stats-collecting loop")

        while True:
            await self._collect_stats()
            await asyncio.sleep(self.COLLECT_INTERVAL_SEC)

    async def _collect_stats(self):
        logger.debug("Start collecting stats")

        chats = await chat_dao.get_chats()

        for chat in chats:
            logger.debug(f"Start collecting stats for channel_id={chat.chat_id}")

            async for message, stats_dto in stats_service.get_message_stats(
                chat.chat_id
            ):
                self.questdb_ingester.save(
                    "stats",
                    symbols={
                        "message_id": str(message.id),
                        "chat_id": str(message.peer_id.channel_id),
                    },
                    columns={
                        "views": stats_dto.views,
                        "reactions": stats_dto.reactions,
                        "forwards": stats_dto.forwards,
                        "replies": stats_dto.replies,
                    },
                )

            logger.debug(f"Finish collecting stats for channel_id={chat.chat_id}")

        logger.debug("Finish collecting stats")

