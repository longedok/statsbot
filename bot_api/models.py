from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Self
import json


@dataclass
class ForwardFromChat:
    chat_id: int
    title: str | None = field(repr=False)
    username: str | None
    type: str = field(repr=False)

    @classmethod
    def from_json(cls, forwrad_from_chat_json: dict) -> Self:
        chat_id = forwrad_from_chat_json["id"]
        title = forwrad_from_chat_json.get("title")
        username = forwrad_from_chat_json.get("username")
        chat_type = forwrad_from_chat_json["type"]
        return cls(chat_id, title, username, chat_type)


@dataclass
class Chat:
    id: int
    title: str | None = field(repr=False)
    type: str

    @classmethod
    def from_json(cls, chat_json: dict) -> Self:
        chat_id = chat_json["id"]
        title = chat_json.get("title")
        chat_type = chat_json["type"]
        return cls(chat_id, title, chat_type)


@dataclass
class Entity:
    offset: int
    length: int
    type: str

    @classmethod
    def from_json(self, entity_json: dict) -> Self:
        offset = entity_json["offset"]
        length = entity_json["length"]
        type = entity_json["type"]
        return Entity(offset, length, type)


@dataclass
class Command:
    command: str
    params: list[str]
    username: str
    entity: Entity

    params_clean: list[Any] = field(default_factory=list, init=False)


@dataclass
class Peer:
    id: int
    username: str | None

    @classmethod
    def from_json(cls, peer_json: dict) -> Self:
        id_ = peer_json["id"]
        username = peer_json.get("username")
        return Peer(id_, username)


@dataclass
class Message:
    text: str | None = field(repr=False)
    message_id: int
    chat: Chat
    from_: Peer
    date: int
    entities: list[Entity]
    forward_from_chat: ForwardFromChat | None

    @classmethod
    def from_json(cls, message_json: dict) -> Self:
        text = message_json.get("text")
        message_id = message_json["message_id"]
        chat = Chat.from_json(message_json["chat"])
        date = message_json["date"]

        entities_json = message_json.get("entities", [])
        if entities_json:
            entities = [Entity.from_json(entity) for entity in entities_json]
        else:
            entities = []

        if forward_json := message_json.get("forward_from_chat"):
            forward_from_chat = ForwardFromChat.from_json(forward_json)
        else:
            forward_from_chat = None

        if from_ := message_json.get("from"):
            from_ = Peer.from_json(from_)
        else:
            from_ = None

        return cls(text, message_id, chat, from_, date, entities, forward_from_chat)

    @cached_property
    def command(self) -> Command | None:
        entities = self.get_entities_by_type("bot_command")
        entity = next(iter(entities), None)

        if not entity:
            return None

        assert self.text

        command_str = self.get_entity_text(entity).lower()
        command_str, _, username = command_str.partition("@")

        params_str = self.text[entity.offset + entity.length + 1 :]
        params = params_str.split() if params_str else []

        return Command(command_str, params, username, entity)

    def get_entities_by_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self.entities if e.type == entity_type]

    def get_entity_text(self, entity: Entity) -> str:
        assert self.text

        offset, length = entity.offset, entity.length
        command_str = self.text[offset + 1 : offset + length].lower()
        return self.text[offset + 1 : offset + length]

    def get_tags(self) -> list[str]:
        entities = self.get_entities_by_type("hashtag")
        tags = []

        for entity in entities:
            tag = self.get_entity_text(entity).lower()
            tags.append(tag)

        return tags


@dataclass
class Callback:
    id: int
    message: Message
    data: dict

    @classmethod
    def from_json(cls, callback_json: dict) -> Self:
        id_ = callback_json.get("id")

        if data := callback_json.get("data"):
            data = json.loads(data)

        if message_json := callback_json.get("message"):
            message = Message.from_json(message_json)
        else:
            message = None

        return Callback(id_, message, data)

