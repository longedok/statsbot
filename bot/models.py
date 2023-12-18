import json
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Self


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
class Message:
    text: str | None = field(repr=False)
    message_id: int
    chat: Chat
    date: int
    entities: list[Entity]

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

        return cls(text, message_id, chat, date, entities)

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

