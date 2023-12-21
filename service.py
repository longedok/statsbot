import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass

from settings import CHAT_ID, DEFAULT_TZ

logger = logging.getLogger(__name__)


default_tz = ZoneInfo(DEFAULT_TZ)


def inline_text(text, max_len=50):
    inline = text[:max_len].replace("\n", " ")
    if len(text) > max_len:
        inline += "..."

    return inline


def get_number(number):
    return number if number is not None else 0


def get_local_time():
    now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    return now.astimezone(default_tz)


def format_date(timestamp):
    local_time = timestamp.astimezone(default_tz)
    return local_time.strftime("%a %d %b %Y %H:%M")


def format_involvement(involvement):
    return f"{involvement}%" if involvement is not None else 'n/a'


@dataclass
class MessageStats:
    views: int
    reactions: int
    forwards: int
    replies: int

    @property
    def total_reactions(self):
        return self.reactions + self.forwards + self.replies


class StatsService:
    def __init__(self, telegram_client):
        self.telegram_client = telegram_client

    async def get_report(self):
        logger.debug("Start building report")
        report = ""
        weekly_stats = []
        async for message in self._get_messages():
            stats = self._get_message_stats(message)
            weekly_stats.append(stats)

            if stats.views > 0:
                involvement = round((stats.total_reactions / stats.views) * 100, 2)
            else:
                involvement = None

            title = inline_text(message.text) if message.text else "..."
            report += f"<b>{title}</b>\n"
            report += f"<i>{format_date(message.date)}</i>\n"
            report += f"<code>{stats.reactions}</code> reactions + "
            report += f"<code>{stats.replies}</code> replies + "
            report += f"<code>{stats.forwards}</code> forwards"
            report += f" = <code>{stats.total_reactions}</code> total\n"
            report += f"<code>{stats.views}</code> views\n"
            report += f"<b>involvement</b> = "
            report += f"<code>{format_involvement(involvement)}</code>\n\n"

        logger.debug("Finished building report")
        return report

    async def _get_messages(self):
        from_date = self._get_from_date()
        logger.debug(
            "Retrieving message history for chat %s from %s", CHAT_ID, from_date,
        )

        async for message in self.telegram_client.iter_messages(
            CHAT_ID, reverse=True, offset_date=from_date
        ):
            yield message
 
    @staticmethod
    def _get_from_date():
        return (get_local_time() - timedelta(weeks=1)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )

    @staticmethod
    def _get_message_stats(message):
        num_views = get_number(message.views)
        num_forwards = get_number(message.forwards)
        if reactions := message.reactions:
            num_reactions = sum(res.count for res in reactions.results)
        else:
            num_reactions = 0

        if replies := message.replies:
            num_replies = replies.replies
        else:
            num_replies = 0

        return MessageStats(num_views, num_reactions, num_forwards, num_replies)

