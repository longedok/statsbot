import asyncio
import logging

logger = logging.getLogger(__name__)


class StatsCollector:
    COLLECT_INTERVAL_SEC = 5 * 60

    def __init__(self, stats_saver, stats_reporter):
        self.stats_saver = stats_saver
        self.stats_reporter = stats_reporter

    async def start(self):
        logger.info("Enter stats-collecting loop")
        while True:
            await self._collect_stats()
            await asyncio.sleep(self.COLLECT_INTERVAL_SEC)

    async def _collect_stats(self):
        logger.info("Start collecting stats")
        async for stats in self.stats_reporter.get_stats():
            self.stats_saver.save(stats)
        logger.info("Finish collecting stats")

