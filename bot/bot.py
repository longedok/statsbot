import logging
import asyncio

from handlers import HandlerRegistry
from settings import CHAT_TITLE
from .models import Message
from .client import BotApiClient

logger = logging.getLogger(__name__)


NOT_FOUND = object()


class Bot:
    def __init__(self, telegram_client, stats_saver):
        self.bot_api = BotApiClient()
        self.telegram_client = telegram_client
        self.stats_saver = stats_saver
        self._channel_id = None

    @property
    def channel_id(self):
        assert self._channel_id is not None, (
            "You must call `find_dialog()` before accessing `channel_id`"
        )

        if self._channel_id is NOT_FOUND:
            return None

        return self._channel_id

    async def start(self):
        if self._channel_id is None:
            await self.find_dialog()
        await asyncio.gather(self._set_commands(), self._process_updates())

    async def find_dialog(self, title=CHAT_TITLE, limit=10):
        logger.info(f"Searching for dialog \"{title}\"")
        dialogs = await self.telegram_client.get_dialogs(limit=limit)
        for dialog in dialogs:
            if title in dialog.name.lower():
                self._channel_id = dialog.entity.id
                logger.info(f"Dialog \"{title}\" found: channel_id={self._channel_id}")
                return dialog
        self._channel_id = NOT_FOUND
        logger.info(f"Dialog \"{title}\" not found")

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
        logger.info("Updates-processing loop shut down")

    async def _process_update(self, update):
        update_id = update.get("update_id")
        logger.info("Start processing update %s: %s", update_id, update)
        if message_json := update.get("message"):
            message = Message.from_json(message_json)
            if command := message.command:
                if handler_cls := HandlerRegistry.get_handler(command.command):
                    handler = handler_cls(self)
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

