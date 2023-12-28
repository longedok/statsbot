import logging

from .database import db

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id SYMBOL CAPACITY 16384,
    username STRING,
    created_at TIMESTAMP
), INDEX (user_id);

CREATE TABLE IF NOT EXISTS chats (
    chat_id SYMBOL CAPACITY 32768,
    title STRING,
    created_at TIMESTAMP
), INDEX (chat_id);

CREATE TABLE IF NOT EXISTS messages (
    message_id SYMBOL CAPACITY 65536,
    chat_id SYMBOL CAPACITY 32768,
    text STRING,
    posted_at TIMESTAMP
),
INDEX(message_id), INDEX(chat_id)
TIMESTAMP (posted_at) PARTITION BY YEAR WAL
DEDUP UPSERT KEYS(posted_at, message_id, chat_id);

CREATE TABLE IF NOT EXISTS stats (
    ts TIMESTAMP,
    message_id SYMBOL CAPACITY 65536,
    chat_id SYMBOL CAPACITY 32768,
    forwards LONG,
    reactions LONG,
    replies LONG
),
INDEX(message_id), INDEX(chat_id)
TIMESTAMP(ts) PARTITION BY MONTH WAL;
"""


async def create_schema():
    logger.info("Start creating database schema")

    await db.execute(SCHEMA)

    logger.info("Finish creating database schema")

