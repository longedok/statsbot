import threading
import time
import logging
from queue import Queue, Empty

from questdb.ingress import Sender, TimestampNanos

from settings import QDB_HOST, QDB_INFLUX_PORT

logger = logging.getLogger(__name__)


class QuestDbIngester(threading.Thread):
    WATERMARK = 1024
    QUEUE_TIMEOUT_SEC = 0.1
    FLUSH_INTERVAL_SEC = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.last_flush = 0
        self.sender = Sender(
            host=QDB_HOST, port=QDB_INFLUX_PORT, auto_flush=self.WATERMARK,
        )
        self.running = True

    def save(self, table, columns, symbols=None, at=None):
        self.queue.put((table, columns, symbols, at))

    def stop(self):
        self.running = False
        self.join()

    def run(self):
        logger.info("Enter QuestDB ingestion loop")
        self.running = True
        with self.sender:
            self.last_flush = time.monotonic()

            while self.running:
                self._process_message()
            if len(self.sender):
                self.sender.flush()
            logger.info("QuestDb ingestion loop shut down")

    def _process_message(self):
        try:
            table, columns, symbols, at = self.queue.get(
                timeout=self.QUEUE_TIMEOUT_SEC
            )
        except Empty:
            return
        else:
            logger.debug(f"Saving a row for table {table}")
            if not at:
                at = TimestampNanos.now()

            self.sender.row(table, columns=columns, symbols=symbols, at=at)

            if not len(self.sender):
                self.last_flush = time.monotonic()
        finally:
            if time.monotonic() - self.last_flush > self.FLUSH_INTERVAL_SEC:
                self.sender.flush()

