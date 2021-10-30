from discord.ext import commands
from discord_slash import SlashContext
from peewee import DoesNotExist

from discordClient.helper import constants
from discordClient.model import Moderator, Settings


class BaseCogs(commands.Cog):

    def __init__(self, bot, name: str):
        self.bot = bot
        self.cogs_name = name
        self.locked_message = {}

    async def retrieve_member(self, discord_user_id: int):
        discord_user = self.bot.get_user(discord_user_id)
        if discord_user is None:
            discord_user = await self.bot.fetch_user(discord_user_id)
        return discord_user

    def disabled(func):
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], SlashContext):
                restriction_model = Settings.get_or_none(guild_id=args[0].guild_id,
                                                         cog=self.cogs_name,
                                                         is_disabled=True)
                if restriction_model is not None:
                    await args[0].send(f"The cog {self.cogs_name} has been disabled on this server", hidden=True)
                    return None
            return await func(self, *args, **kwargs)

        return wrapper

    def moderator_restricted(func):
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], SlashContext):
                try:
                    Moderator.get(Moderator.discord_user_id == args[0].author.id)
                except DoesNotExist:
                    await args[0].send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
                                       f"functionality. {constants.WARNING_EMOJI}", hidden=True)
                    return None
            return await func(self, *args, **kwargs)

        return wrapper

    def guild_administrator_restricted(func):
        async def wrapper(self, *args, **kwargs):
            if isinstance(args[0], SlashContext):
                user_permissions = args[0].channel.permissions_for(args[0].author)
                if not user_permissions.administrator:
                    await args[0].send(content=f"You're an average joe {args[0].author.mention}, you can't use "
                                               f"this command.",
                                       hidden=True)
                    return None
            return await func(self, *args, **kwargs)

        return wrapper
