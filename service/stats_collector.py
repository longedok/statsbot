import asyncio
import logging

from service.stats_service import stats_service

logger = logging.getLogger(__name__)


class StatsCollector:
    COLLECT_INTERVAL_SEC = 5 * 60

    def __init__(self, questdb_ingester, channel_id):
        self.questdb_ingester = questdb_ingester
        self.channel_id = channel_id

    async def start(self):
        logger.info("Enter stats-collecting loop")

        while True:
            await self._collect_stats()
            await asyncio.sleep(self.COLLECT_INTERVAL_SEC)

    async def _collect_stats(self):
        logger.info("Start collecting stats")

        async for message, stats_dto in stats_service.get_message_stats(
            self.channel_id
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

        logger.debug("Finish collecting stats")

