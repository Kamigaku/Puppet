from functools import wraps

from peewee import DoesNotExist

from discordClient.helper import constants
from discordClient.model import Moderator, Settings
from discord.ext.commands import Cog, InteractionContext


class BaseCogs(Cog):

    def __init__(self, bot, name: str):
        self.bot = bot
        self.cogs_name = name
        self.locked_message = {}

    async def retrieve_member(self, discord_user_id: int):
        discord_user = self.bot.get_user(discord_user_id)
        if discord_user is None:
            discord_user = await self.bot.fetch_user(discord_user_id)
        return discord_user

    @staticmethod
    def disabled(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], InteractionContext):
                restriction_model = Settings.get_or_none(guild_id=args[0].guild.id,
                                                         cog=self.cogs_name,
                                                         is_disabled=True)
                if restriction_model is not None:
                    await args[0].send(f"The cog {self.cogs_name} has been disabled on this server", hidden=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def moderator_restricted(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], InteractionContext):
                try:
                    Moderator.get(Moderator.discord_user_id == args[0].author.id)
                except DoesNotExist:
                    await args[0].send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
                                       f"functionality. {constants.WARNING_EMOJI}", hidden=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def guild_administrator_restricted(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], InteractionContext):
                user_permissions = args[0].channel.permissions_for(args[0].author)
                if not user_permissions.administrator:
                    await args[0].send(content=f"You're an average joe {args[0].author.mention}, you can't use "
                                               f"this command.",
                                       hidden=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper
