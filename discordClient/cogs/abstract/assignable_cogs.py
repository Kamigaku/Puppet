from functools import wraps

from discord.ext.commands import InteractionContext
from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Settings


class AssignableCogs(BaseCogs):

    def __init__(self, bot, name):
        super().__init__(bot, name)

    @staticmethod
    def restricted(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if isinstance(self, AssignableCogs) and isinstance(args[0], InteractionContext):
                interaction_context: InteractionContext = args[0]
                settings_model = Settings.get_or_none(guild_id=interaction_context.guild.id,
                                                      cog=self.cogs_name)
                if (settings_model is not None and
                        settings_model.channel_id_restriction is not None and
                        settings_model.channel_id_restriction != interaction_context.channel.id):
                    await interaction_context.send("The command needs to be send in the correct channel",
                                                   ephemeral=True)
                    return None
            return await func(self, *args, **kwargs)
        return wrapper
