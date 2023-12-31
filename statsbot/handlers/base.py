from abc import abstractmethod
from functools import cached_property
from logging import getLogger

from .registry import HandlerRegistry

logger = getLogger("handlers")


class Handler(metaclass=HandlerRegistry):
    key = None
    description = None

    def __init__(self, bot):
        self.bot = bot
        self.update = None

    @cached_property
    def bot_api(self):
        return self.bot.bot_api

    async def handle(self, update):
        logger.info(f"Start handling key '{self.key}'")
        self.update = update
        await self._process_update()
        logger.info(f"Finished handling key '{self.key}'")

    @abstractmethod
    async def _process_update(self):
        ...

    @classmethod
    def as_dict(cls):
        return {"command": cls.key, "description": cls.description}


class MessageHandler(Handler):
    @cached_property
    def message(self):
        return self.update

    @cached_property
    def chat(self):
        return self.update.chat


class CallbackHandler(Handler):
    @cached_property
    def message(self):
        return self.update.message

    @cached_property
    def callback(self):
        return self.update

