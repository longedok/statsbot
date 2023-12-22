from dataclasses import dataclass


@dataclass
class MessageStats:
    message_id: int
    views: int
    reactions: int
    forwards: int
    replies: int

    @property
    def total_reactions(self):
        return self.reactions + self.forwards + self.replies

