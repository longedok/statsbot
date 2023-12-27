from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class StatsDto:
    views: int
    reactions: int
    forwards: int
    replies: int

    @property
    def total_reactions(self):
        return self.reactions + self.forwards + self.replies


@dataclass
class MessageDto:
    message_id: int
    chat_id: int
    text: str
    date: datetime


@dataclass
class ChatDto:
    chat_id: int
    title: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserDto:
    user_id: int
    username: str
    created_at: datetime = field(default_factory=datetime.now)

