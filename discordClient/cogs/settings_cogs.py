import discord
from discord_slash import SlashCommandOptionType, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice

from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Settings


class SettingsCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "settings")

    @cog_ext.cog_slash(name="restrict",
                       description="Restrict cog's command to a specific channel.",
                       options=[
                           create_option(
                               name="cog",
                               description="Specify the name of the cog that will be restricted",
                               option_type=SlashCommandOptionType.STRING,
                               choices=[create_choice(name="Card buy and search",
                                                      value="card"),
                                        create_choice(name="Museum",
                                                      value="museum"),
                                        create_choice(name="Trading",
                                                      value="trade"),
                                        create_choice(name="Announcement",
                                                      value="announcement")],
                               required=True
                           ),
                           create_option(
                               name="channel",
                               description="Specify the channel where the cog will be restricted. No value means "
                                           "suppression.",
                               option_type=SlashCommandOptionType.CHANNEL,
                               required=False
                           )
                       ])
    @BaseCogs.guild_administrator_restricted
    async def restrict(self, ctx: SlashContext, cog: str, channel: discord.abc.GuildChannel = None):
        if channel is None:  # On retire la restriction appliquée si elle existe
            settings_model = Settings.get_or_none(guild_id=ctx.guild_id, cog=cog)
            if settings_model is not None:
                settings_model.channel_id_restriction = None
                settings_model.save()
                await ctx.send(f"The restriction has been removed for the cog \"{cog}\"", hidden=True)
            else:
                await ctx.send(f"The cog \"{cog}\" isn't restricted.", hidden=True)
        else:  # On applique la nouvelle restriction
            if isinstance(channel, discord.TextChannel):
                restriction_model, was_created = Settings.get_or_create(guild_id=ctx.guild_id, cog=cog)
                restriction_model.channel_id_restriction = channel.id
                restriction_model.save()
                await ctx.send(f"The restriction for the cog \"{cog}\" has been updated", hidden=True)
            else:
                await ctx.send("Invalid channel, the restriction needs to be applied to a text channel.", hidden=True)

    @cog_ext.cog_slash(name="disable",
                       description="Disable a cog on your discord.",
                       options=[
                           create_option(
                               name="cog",
                               description="Specify the name of the cog that will be restricted",
                               option_type=SlashCommandOptionType.STRING,
                               choices=[create_choice(name="Trading",
                                                      value="trade")],
                               required=True
                           )])
    @BaseCogs.guild_administrator_restricted
    async def disable(self, ctx: SlashContext, cog: str = None):
        settings_model, was_created = Settings.get_or_create(guild_id=ctx.guild_id, cog=cog)
        settings_model.is_disabled = not settings_model.is_disabled
        settings_model.save()
        if not settings_model.is_disabled:
            await ctx.send(f"The disablement regarding the cog {cog} has been removed.", hidden=True)
        else:
            await ctx.send(f"The cog {cog} has been disabled on your server", hidden=True)
