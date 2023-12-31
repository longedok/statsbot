from telethon.tl.types import PeerChannel
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError

from dao import chat_dao
from dto import ChatDto
from telegram_client import telegram_client

from .exceptions import ChannelPrivateError as ServiceChannelPrivateError


class ChatService:
    SEARCH_RESULTS_LIMIT = 20

    async def get_or_create_channel(self, channel_id, chat_title):
        if chat_dto := await chat_dao.get_chat(channel_id):
            return chat_dto, False

        # search for channel to populate the entity cache
        await self._search(chat_title)

        try:
            # getting the entity to ensure the chat isn't private
            channel_entity = await self._get_channel_entity(channel_id)
        except ChannelPrivateError:
            raise ServiceChannelPrivateError
        else:
            pass
            # TODO: commented out for now to avoid adding arbitrary chats
            # await telegram_client(JoinChannelRequest(channel_entity))

        chat_dto = ChatDto(channel_id, chat_title)
        await chat_dao.create_chat(chat_dto)

        return chat_dto, True

    async def _search(self, query):
        request = SearchRequest(q=query, limit=self.SEARCH_RESULTS_LIMIT)
        return await telegram_client(request)

    @staticmethod
    async def _get_channel_entity(channel_id):
        return await telegram_client.get_entity(PeerChannel(channel_id))

chat_service = ChatService()

