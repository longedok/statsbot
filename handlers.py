import logging
from functools import cached_property
from abc import abstractmethod

from service.stats_reporter import StatsReporter

logger = logging.getLogger(__name__)


class HandlerRegistry(type):
    handlers = {}

    def __new__(cls, name, bases, dct):
        handler_cls = super().__new__(cls, name, bases, dct)
        if handler_cls.command is not None:
            cls.handlers[handler_cls.command] = handler_cls
        return handler_cls

    @classmethod
    def get_handler(cls, command):
        return cls.handlers.get(command)

    @classmethod
    def get_handlers(cls):
        return cls.handlers.values()


class Handler(metaclass=HandlerRegistry):
    command = None
    description = None

    def __init__(self, bot):
        self.bot = bot
        self.message = None

    @cached_property
    def bot_api(self):
        return self.bot.bot_api

    async def handle(self, message):
        logger.info(f"Start handling command /{self.command}")
        self.message = message
        await self._process_message()
        logger.info(f"Finished handling command /{self.command}")

    @abstractmethod
    async def _process_message(self):
        ...

    @classmethod
    def as_dict(cls):
        return {"command": cls.command, "description": cls.description}


class StatsHandler(Handler):
    command = "stats"
    description = "Calculate weekly involvement statistics"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats_reporter = StatsReporter(
            self.bot.telegram_client, self.bot.channel_id
        )

    async def _process_message(self):
        report = await self.stats_reporter.get_report()
        await self.bot_api.post_message(self.message.chat.id, report)


class StartHandler(Handler):
    command = "start"
    description = None
    greeting = '''
Hi there, this bot calculates involvement statistics for your telegram channel.
Use the /stats command to see the weekly statistics.
    '''

    async def _process_message(self):
        await self.bot_api.post_message(self.message.chat.id, self.greeting)

