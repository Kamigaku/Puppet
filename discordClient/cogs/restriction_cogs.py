import discord
from discord.ext.commands import has_permissions, CheckFailure
from discord_slash import SlashCommandOptionType, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice
from peewee import DoesNotExist

from discordClient.cogs.abstract import BaseCogs
from discordClient.model import Restriction


class RestrictionCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "restriction")

    @cog_ext.cog_slash(name="restrict",
                       description="Restrict cog's command to a specific channel.",
                       options=[
                           create_option(
                               name="cog",
                               description="Specify the name of the cog that will be restricted",
                               option_type=SlashCommandOptionType.STRING,
                               choices=[create_choice(name=f"Card buy and search",
                                                      value="card"),
                                        create_choice(name=f"Museum",
                                                      value="museum"),
                                        create_choice(name=f"Trading",
                                                      value="trade")],
                               required=False
                           ),
                           create_option(
                               name="channel",
                               description="Specify the channel where the cog will be restricted. No value means "
                                           "suppression.",
                               option_type=SlashCommandOptionType.CHANNEL,
                               required=False
                           )
                       ])
    async def restrict(self, ctx: SlashContext, cog: str = None, channel: discord.abc.GuildChannel = None):
        user_permissions = ctx.channel.permissions_for(ctx.author)
        if not user_permissions.administrator:
            await ctx.send(content=f"You're an average joe {ctx.author.mention}, you can't use this command.",
                           hidden=True)
            return
        if channel is None:
            try:
                Restriction.get(guild_id=ctx.guild_id, cog=cog).delete_instance()
                await ctx.send(f"The restriction has been removed for the cog \"{cog}\"", hidden=True)
            except DoesNotExist:
                await ctx.send(f"The cog \"{cog}\" isn't restricted.", hidden=True)
        else:
            if isinstance(channel, discord.TextChannel):
                try:
                    restriction = Restriction.get(guild_id=ctx.guild_id, cog=cog)
                    restriction.channel_id = channel.id
                    restriction.save()
                    await ctx.send(f"The restriction for the cog \"{cog}\" has been updated", hidden=True)
                except DoesNotExist:
                    Restriction.create(guild_id=ctx.guild_id, channel_id=channel.id, cog=cog)
                    await ctx.send(f"The restriction for the cog \"{cog}\" has been created", hidden=True)
            else:
                await ctx.send("Invalid channel, the restriction needs to be applied to a text channel.", hidden=True)
