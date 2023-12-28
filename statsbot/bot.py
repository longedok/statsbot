import asyncio
import logging

from bot_api.client import BotApiClient
from bot_api.models import Message, Callback
from handlers import HandlerRegistry
from settings import CHAT_TITLE
from telegram_client import telegram_client

logger = logging.getLogger(__name__)


NOT_FOUND = object()


class Bot:
    def __init__(self):
        self.bot_api = BotApiClient()
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
        dialogs = await telegram_client.get_dialogs(limit=limit)
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
            for update_json in await self.bot_api.get_updates():
                await self._process_update(update_json)
        logger.info("Updates-processing loop shut down")

    async def _process_update(self, update_json):
        update_id = update_json.get("update_id")
        logger.info("Start processing update id=%s: %s", update_id, update_json)

        key = None
        if message_json := update_json.get("message"):
            update = Message.from_json(message_json)
            if command := update.command:
                key = command.command
            elif update.forward_from_chat:
                key = "forward"
        elif callback_json := update_json.get("callback_query"):
            update = Callback.from_json(callback_json)
            key = update.data.get("action")

        if key is None:
            logger.warning("Unrecognized update type, skipping processing")
            return

        if handler_cls := HandlerRegistry.get_handler(key):
            handler = handler_cls(self)
            await handler.handle(update)
        else:
            if command := getattr(update, "command", None):
                await self.bot_api.post_message(
                    update.chat.id,
                    f"Unrecognized command /{command.command}. Say what?",
                )
            logger.warning(f"No handler found for key {key}")

        logger.info("Finished processing update id=%s", update_id)

