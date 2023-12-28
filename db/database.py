from psycopg.rows import dict_row

import logging
from psycopg import AsyncConnection
from contextlib import asynccontextmanager

from settings import QDB_HOST, QDB_POSTGRES_PORT, QDB_USER, QDB_PASSWORD

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._conn = None

    @property
    def conn(self):
        assert self._conn, (
            "No connection to the database. You need to call `connect()` first."
        )
        return self._conn

    async def connect(self):
        logger.info("Connecting to the database")

        self._conn = await AsyncConnection.connect(
            f"postgres://{QDB_USER}@{QDB_HOST}:{QDB_POSTGRES_PORT}/qdb",
            password=QDB_PASSWORD,
            autocommit=True,
            row_factory=dict_row,
        )

        logger.info("Database connection established")

    async def disconnect(self):
        logger.info("Closing database connection")

        await self._conn.close()

        logger.info("Database connection closed")

    @asynccontextmanager
    async def _execute(self, query, params=None):
        async with self.conn.cursor() as cur:
            logging.debug("Executing query %s with params %s", query, params)
            await cur.execute(query, params)
            yield cur

    async def execute(self, query, params=None):
        async with self._execute(query, params):
            return

    async def fetch_one(self, query, params=None):
        async with self._execute(query, params) as cur:
            return await cur.fetchone()

    async def fetch_all(self, query, params=None):
        async with self._execute(query, params) as cur:
            return await cur.fetchall()

db = Database()

