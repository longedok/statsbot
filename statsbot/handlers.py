import asyncio
import json
import logging
from abc import abstractmethod
from enum import Enum
from functools import cached_property

from telethon.tl.types import PeerChannel
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError
from telethon import functions, types

from service.stats_service import stats_service
from dao import chat_dao, user_dao
from dto import ChatDto, UserDto
from telegram_client import telegram_client
from utils import batch

logger = logging.getLogger(__name__)


class HandlerRegistry(type):
    handlers = {}

    def __new__(cls, name, bases, dct):
        handler_cls = super().__new__(cls, name, bases, dct)
        if handler_cls.key is not None:
            assert handler_cls.key not in cls.handlers, (
                f"Handler for key {handler_cls.key} is already registered"
            )
            cls.handlers[handler_cls.key] = handler_cls
        return handler_cls

    @classmethod
    def get_handler(cls, key):
        return cls.handlers.get(key)

    @classmethod
    def get_handlers(cls):
        return cls.handlers.values()


class Handler(metaclass=HandlerRegistry):
    key = None
    description = None

    def __init__(self, bot):
        self.bot = bot
        self.message = None

    @cached_property
    def bot_api(self):
        return self.bot.bot_api

    @cached_property
    def chat(self):
        return self.message.chat

    async def handle(self, message):
        logger.info(f"Start handling key '{self.key}'")
        self.message = message
        await self._process_message()
        logger.info(f"Finished handling key '{self.key}'")

    @abstractmethod
    async def _process_message(self):
        ...

    @classmethod
    def as_dict(cls):
        return {"command": cls.key, "description": cls.description}

MAX_MESSAGE_LENGTH = 4096


def _limit_max_len(message):
    message_len = len(message)
    if message_len > MAX_MESSAGE_LENGTH:
        return message[message_len-MAX_MESSAGE_LENGTH:]

    return message


def _build_chats_keyboard(chats):
    keyboard, buttons = [], []
    for i, chat in enumerate(chats):
        buttons.append({
            "text": chat.title,
            "callback_data": json.dumps({
                "action": "stats",
                "channel_id": chat.chat_id,
            })
        })

        if i % 2 == 1:
            keyboard.append(buttons)
            buttons = []

    if buttons:
        keyboard.append(buttons)

    return keyboard


class StatsHandler(Handler):
    key = "stats"
    description = "Calculate weekly involvement statistics"
    no_chats_reply = """
You have no channels. Please forward a message from a channel to see its stats.
    """

    async def _process_message(self):
        if not (chats := await chat_dao.get_chats()):
            await self.bot_api.post_message(self.chat.id, self.no_chats_reply)
            return

        keyboard = _build_chats_keyboard(chats)

        await self.bot_api.post_message(
            self.chat.id,
            "Select the chat to display the stats for:",
            reply_markup={"inline_keyboard": keyboard},
        )


class StatsCallbackHandler(Handler):
    STATS_PER_MESSAGE = 15
    key = "stats_callback"

    @cached_property
    def callback(self):
        return self.message

    async def _process_message(self):
        if not (channel_id := self.callback.data.get("channel_id")):
            logger.warning("No `channel_id` in callback data, aborting handler")
            return

        message_stats = await stats_service.get_report(channel_id)
        anwser_task = asyncio.create_task(
            self.bot_api.answer_callback(self.callback.id)
        )

        for stats_group in batch(message_stats, n=self.STATS_PER_MESSAGE):
            report = "".join(stats_group)
            message = self.callback.message
            await self.bot_api.post_message(message.chat.id, report)


class StartHandler(Handler):
    key = "start"
    greeting = '''
Hi there, this bot calculates involvement statistics for telegram channels.
Just forward me a message from a channel you want to see the stats for.
Use the /stats command to see stats for your channels at any time.
    '''

    async def _process_message(self):
        peer = self.message.from_
        if not (user_dto := await user_dao.get_user(peer.id)):
            user_dto = UserDto(peer.id, peer.username)
            await user_dao.create_user(user_dto)

        await self.bot_api.post_message(self.chat.id, self.greeting)


class ForwardsHandler(Handler):
    key = "forward"
    response = '''
Channel "{chat_title}" added. Use the command /stats to get the channel's stats.
    '''
    private_response = '''
Channel "{chat_title}" is a private channel.
Please send me an invitation link to the channel so I can join it first.
    '''

    @cached_property
    def forward_from_chat(self):
        return self.message.forward_from_chat

    async def _process_message(self):
        channel_id = self.forward_from_chat.chat_id

        if not (chat_dto := await chat_dao.get_chat(channel_id)):
            # search for channel to populate the entity cache
            await telegram_client(functions.contacts.SearchRequest(
                q=self.forward_from_chat.title, limit=20,
            ))

            # getting the entity to ensure the chat isn't private
            try:
                chat_entity = await telegram_client.get_entity(PeerChannel(channel_id))
            except ChannelPrivateError:
                message = self.private_response.format(
                    chat_title=self.forward_from_chat.title
                )
                await self.bot_api.post_message(self.chat.id, message)
                return
            else:
                pass
                # TODO: commented out for now to avoid adding arbitrary chats
                # await telegram_client(JoinChannelRequest(chat_entity))

            chat_dto = ChatDto(channel_id, self.forward_from_chat.title)
            await chat_dao.create_chat(chat_dto)

        res = await self.bot_api.post_message(
            self.chat.id, self.response.format(chat_title=chat_dto.title)
        )

