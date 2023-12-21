import logging
import asyncio

from handlers import HandlerRegistry
from .models import Message
from .client import BotApiClient

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, telegram_client):
        self.bot_api = BotApiClient()
        self.telegram_client = telegram_client

    async def start(self):
        await asyncio.gather(self._set_commands(), self._process_updates())

    async def _set_commands(self):
        logger.info("Start setting bot commands")
        commands = []
        for handler_cls in HandlerRegistry.get_handlers():
            if not handler_cls.description:
                continue
            commands.append(handler_cls.as_dict())

        if commands:
            await self.bot_api.set_my_commands(commands)
            logger.info(f"Finished setting bot commands: {len(commands)} commands set")
        else:
            logger.warning("No commands to set")

    async def _process_updates(self):
        logger.info("Enter updates-processing loop")
        while True:
            for update in await self.bot_api.get_updates():
                await self._process_update(update)

    async def _process_update(self, update):
        update_id = update.get("update_id")
        logger.info("Start processing update %s: %s", update_id, update)
        if message_json := update.get("message"):
            message = Message.from_json(message_json)
            if command := message.command:
                if handler_cls := HandlerRegistry.get_handler(command.command):
                    handler = handler_cls(self.bot_api, self.telegram_client)
                    await handler.handle(message)
                else:
                    await self.bot_api.post_message(
                        message.chat.id, "Unrecognized command. Say what?",
                    )
                    logger.warning(f"No handler found for command {command.command}")
            else:
                logger.info("No command found, skip processing")
        else:
            logger.info("Unrecognized update type")
        logger.info("Finished processing update %s", update_id)

