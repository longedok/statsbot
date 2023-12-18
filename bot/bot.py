import logging

from utils import get_env, get_env_int
from service import StatsService
from handlers import HandlerRegistry
from .models import Message
from .client import BotApiClient

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, telegram_client):
        self.bot_api = BotApiClient()
        self.telegram_client = telegram_client

    async def start(self):
        await self._set_commands()
        await self._process_updates()

    async def _set_commands(self):
        logger.info("Setting bot commands")
        commands = []
        for handler_cls in HandlerRegistry.get_handlers():
            if not handler_cls.description:
                continue
            commands.append(handler_cls.as_dict())
        if commands:
            resp = await self.bot_api.set_my_commands(commands)

    async def _process_updates(self):
        logger.info("Start processing updates")
        while True:
            for update in await self.bot_api.get_updates():
                await self._process_update(update)

    async def _process_update(self, update):
        logger.info("Processing update %s", update)
        if message_json := update.get("message"):
            message = Message.from_json(message_json)
            if command := message.command:
                if handler_cls := HandlerRegistry.get_handler(command.command):
                    handler = handler_cls(self.bot_api, self.telegram_client)
                    await handler.handle(message)
                else:
                    logger.warning("No handler found for command {command.command}")
            else:
                logger.info("No command found, skip processing")
        else:
            logger.info("Unrecognized update type")

