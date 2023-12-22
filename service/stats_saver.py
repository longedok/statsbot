import threading
import time
import logging
from queue import Queue, Empty

from questdb.ingress import Sender, TimestampNanos

from models import MessageStats
from settings import QDB_HOST, QDB_INFLUX_PORT

logger = logging.getLogger(__name__)


class StatsSaver:
    def save(self, message_stats):
        raise NotImplementError


class QuestDbSaver(StatsSaver, threading.Thread):
    WATERMARK = 1024
    QUEUE_TIMEOUT_SEC = 0.1
    FLUSH_INTERVAL_SEC = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.last_flush = 0
        self.sender = Sender(
            host=QDB_HOST, port=QDB_INFLUX_PORT, auto_flush=self.WATERMARK
        )
        self.running = True

    def save(self, message_stats):
        self.queue.put(message_stats)

    def stop(self):
        self.running = False

    def run(self):
        logger.info("Enter stats-sending loop")
        self.running = True
        with self.sender:
            self.last_flush = time.monotonic()

            while self.running:
                self._process_message()
            if len(self.sender):
                self.sender.flush()
            logger.info("Stats-sending loop shut down")

    def _process_message(self):
        try:
            message_stats = self.queue.get(timeout=self.QUEUE_TIMEOUT_SEC)
        except Empty:
            return
        else:
            logger.debug(
                f"Start saving stats for message_id={message_stats.message_id}"
            )
            self._send_stats(message_stats)

            if not len(self.sender):
                self.last_flush = time.monotonic()
            logger.debug(
                "Finish saving stats for message_id={message_stats.message_id}"
            )
        finally:
            if time.monotonic() - self.last_flush > self.FLUSH_INTERVAL_SEC:
                self.sender.flush()

    def _send_stats(self, message_stats):
        self.sender.row(
            "stats",
            symbols={
                "message_id": str(message_stats.message_id),
            },
            columns={
                "views": message_stats.views,
                "reactions": message_stats.reactions,
                "forwards": message_stats.forwards,
                "replies": message_stats.replies,
            },
            at=TimestampNanos.now(),
        )
