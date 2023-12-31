import asyncio
import logging
import time
from functools import cached_property

from dao import chat_dao, user_dao
from dto import UserDto
from service.chat_service import chat_service
from service.exceptions import ChannelPrivateError
from service.stats_service import stats_service
from utils import batch

from .base import MessageHandler, CallbackHandler
from .registry import HandlerRegistry
from .utils import make_keyboard

logger = logging.getLogger("handlers")


class StartHandler(MessageHandler):
    key = "start"
    replies = {
        "greeting": (
            "Hi there, this bot calculates involvement statistics for telegram "
            "channels.\n"
            "Just forward me a message from a channel you want to see the stats for. "
            "Use the command /channels to see the list of your channels."
        )
    }

    async def _process_update(self):
        peer = self.message.from_
        if not await user_dao.get_user(peer.id):
            await user_dao.create_user(UserDto(peer.id, peer.username))

        await self.reply("greeting")


class ForwardsHandler(MessageHandler):
    key = "forward"
    replies = {
        "success": (
            "Channel \"{channel_title}\" added. Use the command /channels to get the "
            "channel's stats."
        ),
        "already_exists": (
            "Channel \"{channel_title}\" already exists in the list of your channels. "
            "Use the command /channels to get the channel's stats."
        ),
        "channel_private": (
            "Channel \"{channel_title}\" is a private channel.\n\n"
            "Please send me an invitation link to the channel so I can join it first."
        )
    }

    @cached_property
    def forward_from_chat(self):
        return self.message.forward_from_chat

    async def _process_update(self):
        channel_id = self.forward_from_chat.chat_id
        channel_title = self.forward_from_chat.title

        try:
            channel, created = await chat_service.get_or_create_channel(
                channel_id, channel_title
            )
        except ChannelPrivateError:
            await self.reply("channel_private", channel_title=channel_title)
            return

        if not created:
            await self.reply("already_exists", channel_title=channel.title)
            return

        await self.reply("success", channel_title=channel.title)


class ChannelsHandler(MessageHandler):
    key = "channels"
    description = "Show the list of channels"
    replies = {
        "no_channels": (
            "You have no channels. Please forward a message from a channel to see its "
            "stats."
        )
    }

    async def _process_update(self):
        if not (chats := await chat_dao.get_chats()):
            await self.reply("no_channels")
            return

        keyboard = self._build_chats_keyboard(chats)

        await self.bot_api.post_message(
            self.chat.id,
            "Select the channel to display the stats for:",
            reply_markup={"inline_keyboard": keyboard},
        )

    @staticmethod
    def _build_chats_keyboard(chats):
        return make_keyboard(
            (
                chat.title, {"a": "select_channel", "cid": chat.chat_id}
            ) for chat in chats
        )


class SelectChannelHandler(CallbackHandler):
    key = "select_channel"

    response = (
        "Select the time period to display the stats for channel \"{channel}\":"
    )

    async def _process_update(self):
        if not (channel_id := self.callback.data.get("cid")):
            logger.warning("No `cid` in callback data, aborting handler")
            return

        keyboard = make_keyboard([
            ("1 week", {"a": "get_stats", "cid": channel_id, "p": "w"}),
            ("1 month", {"a": "get_stats", "cid": channel_id, "p": "m"}),
        ])

        chat_dto = await chat_dao.get_chat(channel_id)

        if not chat_dto:
            logger.warnring(
                f"Channel channel_id={channel_id} not found, aborting handler"
            )
            return

        res = await asyncio.gather(
            self.bot_api.answer_callback(self.callback.id),
            self.bot_api.edit_message_text(
                self.message.chat.id,
                self.message.message_id,
                self.response.format(channel=chat_dto.title),
                reply_markup={"inline_keyboard": keyboard},
            )
        )


class GetStatsHandler(CallbackHandler):
    key = "get_stats"
    replies = {
        "no_messages": (
            "No messages found in the selected time period for channel "
            "\"{channel_title}\"."
        )
    }

    STATS_PER_MESSAGE = 15
    POSTING_DELAY_SEC = 0.5

    async def _process_update(self):
        if not (channel_id := self.callback.data.get("cid")):
            logger.warning("No `cid` in callback data, aborting handler")
            return

        if not (period := self.callback.data.get("p")):
            logger.warning("No `p` in callback data, aborting handler")
            return

        if period == "w":
            weeks_back = 1
        elif period == "m":
            weeks_back = 4
        else:
            logger.warning(f"Invalid `period` \"{period}\", aborting handler")
            return

        message_stats = await stats_service.get_report(channel_id, weeks_back)
        response_task = asyncio.gather(
            self.bot_api.delete_message(self.message.chat.id, self.message.message_id),
            self.bot_api.answer_callback(self.callback.id)
        )

        if not message_stats:
            chat_dto = await chat_dao.get_chat(channel_id)
            await asyncio.gather(
                self.reply("no_messages", channel_title=chat_dto.title),
                response_task,
            )
            return

        await asyncio.gather(self.post_stats(message_stats), response_task)

    async def post_stats(self, message_stats):
        num_messages = (len(message_stats) // self.STATS_PER_MESSAGE) + 1
        groups = batch(message_stats, n=self.STATS_PER_MESSAGE)
        for i, stats_group in enumerate(groups):
            message_text = "".join(stats_group)
            start = time.monotonic()
            await self.bot_api.post_message(self.message.chat.id, message_text)
            elapsed = time.monotonic() - start
            if i < num_messages - 1:
                sleep_time = self.POSTING_DELAY_SEC - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

