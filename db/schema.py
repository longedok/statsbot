import logging

from .database import db

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id LONG,
    username STRING,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id LONG,
    title STRING,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    message_id LONG,
    chat_id LONG,
    text STRING,
    posted_at TIMESTAMP
)
TIMESTAMP (posted_at) PARTITION BY YEAR WAL
DEDUP UPSERT KEYS(posted_at, message_id, chat_id);

CREATE TABLE IF NOT EXISTS stats (
    ts TIMESTAMP,
    message_id LONG,
    chat_id LONG,
    forwards LONG,
    reactions LONG,
    replies LONG
)
TIMESTAMP(ts)
PARTITION BY MONTH;
"""


async def create_schema():
    logger.info("Start creating database schema")

    await db.execute(SCHEMA)

    logger.info("Finish creating database schema")

