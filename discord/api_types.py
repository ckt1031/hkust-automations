from datetime import datetime

import msgspec


class Author(msgspec.Struct):
    # id: str
    username: str
    bot: bool | None = None


class Embed(msgspec.Struct):
    type: str
    title: str | None = None
    description: str | None = None


class DiscordChannelMessageListItem(msgspec.Struct):
    id: str
    type: int
    content: str
    author: Author
    timestamp: datetime
    embeds: list[Embed]


class DiscordChannelInfo(msgspec.Struct):
    id: str
    name: str
