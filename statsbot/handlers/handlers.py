import asyncio
import json
import logging
from functools import cached_property

from telethon.tl.types import PeerChannel
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError

from dao import chat_dao, user_dao
from dto import ChatDto, UserDto
from service.stats_service import stats_service
from telegram_client import telegram_client
from utils import batch

from .registry import HandlerRegistry
from .base import MessageHandler, CallbackHandler

logger = logging.getLogger("handlers")


class StartHandler(MessageHandler):
    key = "start"

    greeting = (
        "Hi there, this bot calculates involvement statistics for telegram "
        "channels.\n"
        "Just forward me a message from a channel you want to see the stats for. "
        "Use the command /channels to see the list of your channels."
    )

    async def _process_update(self):
        peer = self.message.from_
        if not await user_dao.get_user(peer.id):
            await user_dao.create_user(UserDto(peer.id, peer.username))

        await self.bot_api.post_message(self.chat.id, self.greeting)


class ForwardsHandler(MessageHandler):
    key = "forward"

    response_success = (
        "Channel \"{chat_title}\" added. Use the command /channels to get the channel's"
        " stats."
    )
    response_private = (
        "Channel \"{chat_title}\" is a private channel.\n\n"
        "Please send me an invitation link to the channel so I can join it first."
    )

    SEARCH_RESULTS_LIMIT = 20

    @cached_property
    def forward_from_chat(self):
        return self.message.forward_from_chat

    async def _process_update(self):
        channel_id = self.forward_from_chat.chat_id

        if not (chat_dto := await chat_dao.get_chat(channel_id)):
            chat_title = self.forward_from_chat.title
            # search for channel to populate the entity cache
            await self._search(chat_title)

            try:
                # getting the entity to ensure the chat isn't private
                channel_entity = await self._get_channel_entity(channel_id)
            except ChannelPrivateError:
                await self.bot_api.post_message(
                    self.chat.id, self.response_private.format(chat_title=chat_title)
                )
                return
            else:
                pass
                # TODO: commented out for now to avoid adding arbitrary chats
                # await telegram_client(JoinChannelRequest(channel_entity))

            chat_dto = ChatDto(channel_id, chat_title)
            await chat_dao.create_chat(chat_dto)

        await self.bot_api.post_message(
            self.chat.id, self.response_success.format(chat_title=chat_dto.title)
        )

    async def _search(self, query):
        request = SearchRequest(q=query, limit=self.SEARCH_RESULTS_LIMIT)
        return await telegram_client(request)

    async def _get_channel_entity(self, channel_id):
        return await telegram_client.get_entity(PeerChannel(channel_id))


class ChannelsHandler(MessageHandler):
    key = "channels"
    description = "Show the list of channels"

    response_no_channels = (
        "You have no channels. Please forward a message from a channel to see its "
        "stats."
    )

    async def _process_update(self):
        if not (chats := await chat_dao.get_chats()):
            await self.bot_api.post_message(self.chat.id, self.response_no_channels)
            return

        keyboard = self._build_chats_keyboard(chats)

        await self.bot_api.post_message(
            self.chat.id,
            "Select the channel to display the stats for:",
            reply_markup={"inline_keyboard": keyboard},
        )

    @staticmethod
    def _build_chats_keyboard(chats):
        keyboard, buttons = [], []
        for i, chat in enumerate(chats):
            buttons.append({
                "text": chat.title,
                "callback_data": json.dumps({
                    "action": "select_channel",
                    "channel_id": chat.chat_id,
                })
            })

            if i % 2 == 1:
                keyboard.append(buttons)
                buttons = []

        if buttons:
            keyboard.append(buttons)

        return keyboard


class SelectChannelHandler(CallbackHandler):
    key = "select_channel"

    response_no_message = (
        "No messages found in the selected time period for channel "
        "\"{channel_title}\"."
    )

    STATS_PER_MESSAGE = 15

    async def _process_update(self):
        if not (channel_id := self.callback.data.get("channel_id")):
            logger.warning("No `channel_id` in callback data, aborting handler")
            return

        message_stats = await stats_service.get_report(channel_id)
        anwser_task = asyncio.create_task(
            self.bot_api.answer_callback(self.callback.id)
        )

        message = self.callback.message
        if not message_stats:
            chat_dto = await chat_dao.get_chat(channel_id)
            await self.bot_api.post_message(
                message.chat.id,
                self.response_no_message.format(channel_title=chat_dto.title),
            )
            return

        for stats_group in batch(message_stats, n=self.STATS_PER_MESSAGE):
            report = "".join(stats_group)
            await self.bot_api.post_message(message.chat.id, report)

