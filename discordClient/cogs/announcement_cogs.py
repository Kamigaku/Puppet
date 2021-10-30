from discord import Embed, NotFound, Forbidden, HTTPException
from discord_slash import SlashCommandOptionType, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Settings


class AnnouncementCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "announcement")

    @cog_ext.cog_slash(name="announce",
                       description="Display a message on all discord where the bot is.",
                       options=[
                           create_option(
                               name="message_id",
                               description="Specify the id of the message to display everywhere",
                               option_type=SlashCommandOptionType.STRING,
                               required=True
                           )
                       ])
    @BaseCogs.moderator_restricted
    async def announce(self, ctx: SlashContext, message_id: str):
        try:
            message = await ctx.channel.fetch_message(int(message_id))
            guild_sent, guild_numbers = await self.announce_everywhere(message.content, message.author.avatar_url)
            await ctx.send(f"The announcement have been sent to {guild_sent} out of {guild_numbers} guild(s).",
                           hidden=True)
        except NotFound:
            await ctx.send("Could not retrieve the message. Please ensure that you are sending the command from the "
                           "same channel than the message.",
                           hidden=True)
        except Forbidden:
            await ctx.send("Could not retrieve the message. You don't have enough permissions to read the message.",
                           hidden=True)
        except HTTPException:
            await ctx.send("Could not retrieve the message. Http exception triggered, please contact the admins.",
                           hidden=True)

    async def announce_everywhere(self, content: str, image_url: str) -> [int, int]:
        guild_numbers = len(self.bot.guilds)
        guild_sent = 0

        message_content = f"{constants.REPORT_EMOJI} Puppet has a new announcement for you {constants.REPORT_EMOJI}"
        embed = Embed()
        embed.description = content
        embed.set_author(name="Puppet announcement")
        embed.set_thumbnail(url=image_url)

        for guild in self.bot.guilds:
            restriction_model = Settings.get_or_none(guild_id=guild.id, cog=self.cogs_name)
            if restriction_model is not None:
                announcement_channel = guild.get_channel(restriction_model.channel_id_restriction)
                await announcement_channel.send(content=message_content, embed=embed)
                guild_sent += 1
            else:
                for member in guild.members:
                    if not member.bot and member.guild_permissions.administrator:
                        await member.send(f"{constants.REPORT_EMOJI} An announcement regarding Puppet bot as been made"
                                          f" but you haven't set a channel to receive this announcement. In order for "
                                          f"Puppet to work properly, please create a TextChannel on your discord to "
                                          f"ensure to receive the latest news. {constants.REPORT_EMOJI}")
        return guild_sent, guild_numbers
