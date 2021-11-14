from typing import List

from discord import Embed, NotFound, Forbidden, HTTPException, Message
from discord_slash import SlashCommandOptionType, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Settings
from discordClient.views import ViewWithReactions, AnnouncementEmbedRender


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
            messages_sent, guild_numbers = await self.announce_everywhere(message.content, message.author.avatar_url)
            await ctx.send(f"The announcement have been sent to {len(messages_sent)} out of {guild_numbers} guild(s).",
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

    async def announce_everywhere(self, content: str, image_url: str) -> [List[Message], int]:
        announce_render = AnnouncementEmbedRender(content=content,
                                                  image_url=image_url)
        announce_view = ViewWithReactions(puppet_bot=self.bot,
                                          elements_to_display=None,
                                          render=announce_render)
        return await announce_everywhere(self.bot, self.cogs_name, announce_view)


async def announce_everywhere(bot, cogs_name: str, view: ViewWithReactions) -> [List[Message], int]:
    guild_numbers = len(bot.guilds)
    messages_sent = []
    for guild in bot.guilds:
        restriction_model = Settings.get_or_none(guild_id=guild.id, cog=cogs_name)
        if restriction_model is not None:
            announcement_channel = guild.get_channel(restriction_model.channel_id_restriction)
            message_sent = await view.display_menu(announcement_channel)
            #await announcement_channel.send(content=msg_content, embed=embed)
            messages_sent.append(message_sent)
        else:
            for member in guild.members:
                if not member.bot and member.guild_permissions.administrator:
                    await member.send(f"{constants.REPORT_EMOJI} An announcement regarding Puppet bot as been made"
                                      f" but you haven't set a channel to receive it. In order for "
                                      f"Puppet to work properly, please create a TextChannel on your discord to "
                                      f"ensure to receive the latest news. {constants.REPORT_EMOJI}")
    return messages_sent, guild_numbers


async def announce_in_guild(bot, cogs_name: str, view: ViewWithReactions, guild_id: int) -> bool:
    guild = bot.get_guild(guild_id)
    if guild is not None:
        restriction_model = Settings.get_or_none(guild_id=guild.id, cog=cogs_name)
        if restriction_model is not None:
            announcement_channel = guild.get_channel(restriction_model.channel_id_restriction)
            await view.display_menu(announcement_channel)
            #await announcement_channel.send(content=msg_content, embed=embed)
            return True
        else:
            for member in guild.members:
                if not member.bot and member.guild_permissions.administrator:
                    await member.send(f"{constants.REPORT_EMOJI} An announcement regarding Puppet bot as been made"
                                      f" but you haven't set a channel to receive it. In order for "
                                      f"Puppet to work properly, please create a TextChannel on your discord to "
                                      f"ensure to receive the latest news. {constants.REPORT_EMOJI}")
    return False
