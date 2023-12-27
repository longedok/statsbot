from datetime import datetime
from dto import ChatDto, UserDto
from db import db


def to_timestamp(date):
    return int(date.timestamp() * 1e6)


class BaseDao:
    INSERT_SQL = """
        INSERT INTO {table}
            ({fields})
        VALUES
            ({values});
    """

    def __init__(self, db):
        self.db = db

    def _make_insert_sql(self, table, fields, values=None):
        fields_str = ",".join(fields)
        if values is None:
            values_str = ",".join(["%s"] * len(fields))
        else:
            values_str = ",".join(values)

        return self.INSERT_SQL.format(
            table=table, fields=fields_str, values=values_str
        )

    async def _insert(self, table, fields, values):
        sql = self._make_insert_sql(table, fields)
        await self.db.execute(sql, values)


class MessageDao(BaseDao):
    async def create_message(self, message_dto):
        return await self._insert(
            "messages",
            ("message_id", "chat_id", "text", "posted_at"),
            (
                message_dto.message_id,
                message_dto.chat_id,
                message_dto.text,
                to_timestamp(message_dto.date)
            ),
        )

message_dao = MessageDao(db)


class ChatDao(BaseDao):

    async def get_chat(self, chat_id):
        sql = """
        SELECT chat_id, title, created_at FROM chats WHERE chat_id = %s;
        """

        if record := await self.db.fetch_one(sql, (chat_id,)):
            return self._make_chat_dto(record)

        return None

    async def get_chats(self):
        sql = """
        SELECT chat_id, title, created_at FROM chats;
        """

        chats = []
        for record in await self.db.fetch_all(sql):
            chat_dto = self._make_chat_dto(record)
            chats.append(chat_dto)

        return chats

    @staticmethod
    def _make_chat_dto(record):
        return ChatDto(record[0], record[1], record[2])

    async def create_chat(self, chat_dto):
        return await self._insert(
            "chats",
            ("chat_id", "title", "created_at"),
            (
                chat_dto.chat_id,
                chat_dto.title,
                to_timestamp(chat_dto.created_at),
            ),
        )

chat_dao = ChatDao(db)


class UserDao(BaseDao):
    async def get_user(self, user_id):
        sql = """
        SELECT user_id, username, created_at FROM users WHERE user_id = %s;
        """

        if record := await self.db.fetch_one(sql, (user_id,)):
            return UserDto(record[0], record[1], record[2])

        return None

    async def create_user(self, user_dto):
        return await self._insert(
            "users",
            ("user_id", "username", "created_at"),
            (
                user_dto.user_id,
                user_dto.username,
                to_timestamp(user_dto.created_at),
            ),
        )

user_dao = UserDao(db)

