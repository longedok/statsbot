from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

from dao import message_dao
from dto import StatsDto, MessageDto
from settings import DEFAULT_TZ
from telegram_client import telegram_client

logger = logging.getLogger(__name__)
default_tz = ZoneInfo(DEFAULT_TZ)


def _inline_text(text, max_len=50):
    inline = text[:max_len].replace("\n", " ")
    if len(text) > max_len:
        inline += "..."

    return inline


def _get_number(number):
    return number if number is not None else 0


def _get_local_time():
    now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    return now.astimezone(default_tz)


def _format_date(timestamp):
    local_time = timestamp.astimezone(default_tz)
    return local_time.strftime("%a %d %b %Y %H:%M")


def _format_involvement(involvement):
    return f"{involvement}%" if involvement is not None else 'n/a'


def _make_message_dto(message):
    return MessageDto(
        message.id,
        message.peer_id.channel_id,
        message.text,
        message.date,
    )


def _make_stats_dto(message):
    num_views = _get_number(message.views)
    num_forwards = _get_number(message.forwards)
    if reactions := message.reactions:
        num_reactions = sum(res.count for res in reactions.results)
    else:
        num_reactions = 0

    if replies := message.replies:
        num_replies = replies.replies
    else:
        num_replies = 0

    return StatsDto(num_views, num_reactions, num_forwards, num_replies)


class StatsService:
    async def get_report(self, channel_id, weeks_back=1):
        logger.debug("Start building report")
        lines = []
        async for message, stats in self.get_message_stats(channel_id, weeks_back):
            if stats.views > 0:
                involvement = round((stats.total_reactions / stats.views) * 100, 2)
            else:
                involvement = None

            title = _inline_text(message.raw_text) if message.raw_text else "..."
            line = f"<b>{title}</b>\n"
            line += f"<i>{_format_date(message.date)}</i>\n"
            line += f"<code>{stats.reactions}</code> reactions + "
            line += f"<code>{stats.replies}</code> replies + "
            line += f"<code>{stats.forwards}</code> forwards"
            line += f" = <code>{stats.total_reactions}</code> total\n"
            line += f"<code>{stats.views}</code> views\n"
            line += f"<b>involvement</b> = "
            line += f"<code>{_format_involvement(involvement)}</code>\n\n"
            lines.append(line)

        logger.debug("Finished building report")
        return lines

    async def get_message_stats(self, channel_id, weeks_back=1):
        async for message in telegram_client.iter_messages(
            channel_id, reverse=True, offset_date=self._get_from_date(weeks_back)
        ):
            message_dto = _make_message_dto(message)
            await message_dao.create_message(message_dto)
            yield message, _make_stats_dto(message)

    @staticmethod
    def _get_from_date(weeks_back):
        return (_get_local_time() - timedelta(weeks=weeks_back)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )

stats_service = StatsService()

