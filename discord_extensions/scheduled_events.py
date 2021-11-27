from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any

import discord.abc
from discord.ext.commands import Bot
from discord.http import Route


class ScheduledEventPrivacyLevel(Enum):
    GUILD_ONLY = 2


class ScheduledEventStatus(Enum):
    SCHEDULED = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELED = 4


class ScheduledEventEntityType(Enum):
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3


@dataclass
class ScheduledEventEntityMetadata:
    location: str | None = None

    @classmethod
    def from_payload(cls, data: dict[str, Any] | None):
        if data is None:
            return cls()
        return cls(**data)


class ScheduledEvent:

    def __init__(self, bot: Bot, data: dict[str, Any]):
        self.id: int = int(data["id"])
        self.guild_id: int = int(data["guild_id"])
        self.channel_id: int | None = int(data["channel_id"]) if data["channel_id"] is not None else None
        self.creator_id: int | None = int(data["creator_id"]) if data["creator_id"] is not None else None
        self.name: str = data["name"]
        self.description: str = data.get("description")
        self.scheduled_start_time: datetime = datetime.fromisoformat(data['scheduled_start_time'])
        self.scheduled_end_time: str | None = datetime.fromisoformat(
            data['scheduled_end_time']) if data["scheduled_end_time"] is not None else None
        self.privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel(int(data["privacy_level"]))
        self.status: ScheduledEventStatus = ScheduledEventStatus(int(data["status"]))
        self.entity_type: ScheduledEventEntityType = ScheduledEventEntityType(int(data["entity_type"]))
        self.entity_id: int | None = int(data["entity_id"]) if data["entity_id"] is not None else None
        self.entity_metadata: ScheduledEventEntityMetadata = ScheduledEventEntityMetadata.from_payload(
            data['entity_metadata'])
        self.creator: discord.abc.User | None = bot.get_user(self.creator_id)
        if "user_count" in data:
            self.user_count: int | None = int(data["user_count"]) if data["user_count"] is not None else None
        else:
            self.user_count: int | None = None

    @classmethod
    async def fetch_all(cls, bot: Bot, guild_id: int, with_user_count: bool = False) -> list['ScheduledEvent']:
        """
        Returns a list of guild scheduled event objects for the given guild.
        """
        result = await bot._connection.http.request(
            Route('GET',
                  '/guilds/{guild_id}/scheduled-events',
                  guild_id=guild_id),
            params={"with_user_count": str(with_user_count)})
        return [cls(bot, data) for data in result]

    @classmethod
    async def create(cls,
                     bot: Bot,
                     guild_id: int,
                     name: str,
                     privacy_level: ScheduledEventPrivacyLevel,
                     scheduled_start_time: datetime,
                     scheduled_end_time: datetime,
                     entity_type: ScheduledEventEntityType,
                     entity_metadata: ScheduledEventEntityMetadata,
                     channel_id: int | None = None,
                     description: str | None = None) -> 'ScheduledEvent':
        """
        Create a guild scheduled event in the guild. Returns a guild scheduled event object on success.
        """
        data = {
            "name": name,
            "privacy_level": privacy_level.value,
            "scheduled_start_time": scheduled_start_time.isoformat(),
            "scheduled_end_time": scheduled_end_time.isoformat(),
            "entity_type": entity_type.value
        }
        if channel_id is not None:
            data["channel_id"] = channel_id
        if entity_metadata is not None:
            data["entity_metadata"] = asdict(entity_metadata)
        if description is not None:
            data["description"] = description
        result = await bot._connection.http.request(
            Route('POST',
                  '/guilds/{guild_id}/scheduled-events',
                  guild_id=guild_id),
            json=data)
        return cls(bot, result)

    @classmethod
    async def fetch(cls, bot: Bot, guild_id: int, guild_scheduled_event_id: int) -> 'ScheduledEvent':
        """
        Get a guild scheduled event. Returns a guild scheduled event object on success.
        """
        result = await bot._connection.http.request(
            Route('GET',
                  '/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}',
                  guild_id=guild_id,
                  guild_scheduled_event_id=guild_scheduled_event_id))
        return cls(bot, result)

    @classmethod
    async def edit(cls,
                   bot: Bot,
                   guild_id: int,
                   guild_scheduled_event_id: int,
                   channel_id: int | None = None,
                   entity_metadata: ScheduledEventEntityMetadata | None = None,
                   name: str | None = None,
                   privacy_level: ScheduledEventPrivacyLevel | None = None,
                   scheduled_start_time: datetime | None = None,
                   scheduled_end_time: datetime | None = None,
                   entity_type: ScheduledEventEntityType | None = None,
                   description: str | None = None,
                   status: ScheduledEventStatus | None = None) -> 'ScheduledEvent':
        """
        Create a guild scheduled event in the guild. Returns a guild scheduled event object on success.
        """
        data = {}
        if name is not None:
            data["name"] = name
        if privacy_level is not None:
            data["privacy_level"] = privacy_level.value
        if scheduled_start_time is not None:
            data["scheduled_start_time"] = scheduled_start_time.isoformat()
        if entity_type is not None:
            data["entity_type"] = entity_type.value
        if channel_id is not None:
            data["channel_id"] = channel_id
        if entity_metadata is not None:
            data["entity_type"] = asdict(entity_metadata)
        if scheduled_end_time is not None:
            data["scheduled_end_time"] = scheduled_end_time.isoformat()
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status.value
        result = await bot._connection.http.request(
            Route('PATCH',
                  '/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}',
                  guild_id=guild_id,
                  guild_scheduled_event_id=guild_scheduled_event_id),
            json=data)
        return cls(bot, result)

    @classmethod
    async def delete(cls, bot: Bot, guild_id: int, guild_scheduled_event_id: int):
        """
        Delete a guild scheduled event. Returns a 204 on success.
        """
        result = await bot._connection.http.request(
            Route('DELETE',
                  '/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}',
                  guild_id=guild_id,
                  guild_scheduled_event_id=guild_scheduled_event_id),)
        return result  # TODO: à vérifier

    @classmethod
    async def fetch_users(cls,
                          bot: Bot,
                          guild_id: int,
                          guild_scheduled_event_id: int,
                          limit: int = 100,
                          with_member: bool = False,
                          before: int | None = None,
                          after: int | None = None) -> tuple[list[discord.User], list[discord.Member] | None]:
        """
        Get a list of guild scheduled event users subscribed to a guild scheduled event.
        Returns a list of guild scheduled event user objects on success.
        Guild member data, if it exists, is included if the with_member query parameter is set.
        """
        data = {
            "limit": limit,
            "with_member": str(with_member)
        }
        if before is not None:
            data["before"] = before
        if after is not None:
            data["after"] = after
        result = await bot._connection.http.request(
            Route('GET',
                  '/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/users',
                  guild_id=guild_id,
                  guild_scheduled_event_id=guild_scheduled_event_id),
            params=data)
        users = [discord.User(state=bot._connection, data=entry["user"]) for entry in result]
        members = None
        if with_member:
            members = []
            for entry in result:
                member_json = entry["member"]
                member_json["user"] = entry["user"]
                members.append(discord.Member(state=bot._connection, data=member_json, guild=guild_id))
        return users, members
        #return cls(bot, result)
