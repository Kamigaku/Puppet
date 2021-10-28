from discord_slash import SlashContext
from peewee import DoesNotExist

from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Restriction


class AssignableCogs(BaseCogs):

    def __init__(self, bot, name):
        super().__init__(bot, name)

    def restricted(func):
        async def wrapper(self, *args, **kwargs):
            if isinstance(self, AssignableCogs) and isinstance(args[0], SlashContext):
                if not self.check_assignation(args[0]):
                    await args[0].send("The command needs to be send in the correct channel", hidden=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper

    def check_assignation(self, ctx: SlashContext) -> bool:
        try:
            Restriction.get(guild_id=ctx.guild_id, channel_id=ctx.channel_id, cog=self.cogs_name)
            return False
        except DoesNotExist:
            return True
