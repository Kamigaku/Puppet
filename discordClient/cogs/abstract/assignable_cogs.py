from discord_slash import SlashContext

from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Settings


class AssignableCogs(BaseCogs):

    def __init__(self, bot, name):
        super().__init__(bot, name)

    def restricted(func):
        async def wrapper(self, *args, **kwargs):
            if isinstance(self, AssignableCogs) and isinstance(args[0], SlashContext):
                settings_model = Settings.get_or_none(guild_id=args[0].guild_id,
                                                      cog=self.cogs_name)
                if (settings_model is not None and
                        settings_model.channel_id_restriction is not None and
                        settings_model.channel_id_restriction != args[0].channel_id):
                    await args[0].send("The command needs to be send in the correct channel", hidden=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper
