import discord

from discord.ext.commands import slash_command, InteractionContext, ApplicationCommandField
from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Settings


class SettingsCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "settings")

    @slash_command(description="Restrict cog's command to a specific channel.",
                   is_global=True)
    @BaseCogs.guild_administrator_restricted
    async def restrict(self,
                       interaction: InteractionContext,
                       cog: str = ApplicationCommandField(description="Specify the name of the cog that will be "
                                                                      "restricted",
                                                          required=True,
                                                          values={"Card buy and search": "card",
                                                                  "Museum": "museum",
                                                                  "Trading": "trading",
                                                                  "Announcement": "announcement",
                                                                  "Event": "event"}),
                       channel: discord.abc.GuildChannel = ApplicationCommandField(description="Specify the channel "
                                                                                               "where the cog will be "
                                                                                               "restricted. No value "
                                                                                               "means suppression.",
                                                                                   default_value=None)):
        if channel is None:  # On retire la restriction appliquée si elle existe
            settings_model = Settings.get_or_none(guild_id=interaction.guild.id,
                                                  cog=cog)
            if settings_model is not None:
                settings_model.channel_id_restriction = None
                settings_model.save()
                await interaction.send(content=f"The restriction has been removed for the cog \"{cog}\"",
                                       ephemeral=True)
            else:
                await interaction.send(content=f"The cog \"{cog}\" isn't restricted.",
                                       ephemeral=True)
        else:  # On applique la nouvelle restriction
            if isinstance(channel, discord.TextChannel):
                restriction_model, was_created = Settings.get_or_create(guild_id=interaction.guild.id,
                                                                        cog=cog)
                restriction_model.channel_id_restriction = channel.id
                restriction_model.save()
                await interaction.send(content=f"The restriction for the cog \"{cog}\" has been updated",
                                       ephemeral=True)
            else:
                await interaction.send(content="Invalid channel, the restriction needs to be applied to a text "
                                               "channel.",
                                       ephemeral=True)

    @slash_command(description="Disable a cog on your discord.",
                   is_global=True)
    @BaseCogs.guild_administrator_restricted
    async def disable(self,
                      interaction: InteractionContext,
                      cog: str = ApplicationCommandField(description="Specify the name of the cog that will "
                                                                     "be disabled or re-enabled",
                                                         required=True,
                                                         values={"Trading": "trade"})):
        settings_model, was_created = Settings.get_or_create(guild_id=interaction.guild.id,
                                                             cog=cog)
        settings_model.is_disabled = not settings_model.is_disabled
        settings_model.save()
        if not settings_model.is_disabled:
            await interaction.send(content=f"The cog {cog} has been enabled on your server.",
                                   ephemeral=True)
        else:
            await interaction.send(content=f"The cog {cog} has been disabled on your server",
                                   ephemeral=True)


def setup(bot):
    bot.add_cog(SettingsCogs(bot))
