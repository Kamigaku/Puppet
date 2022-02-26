from typing import List

from discord import NotFound, Forbidden, HTTPException, Message
from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Settings
from discordClient.views import AnnouncementEmbedRender
from discordClient.views.view import ViewWithHiddenData
from discord.ext.commands import slash_command, ApplicationCommandField, InteractionContext


class AnnouncementCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "announcement")

    @slash_command(description="Display a message on all discord where the bot is.",
                   is_global=True)
    @BaseCogs.moderator_restricted
    async def announce(self,
                       ctx: InteractionContext,
                       message_id: str = ApplicationCommandField(description="Display a message on all discord "
                                                                             "where the bot is.",
                                                                 required=True)):
        try:
            message: Message = await ctx.channel.fetch_message(int(message_id))
            messages_sent, guild_numbers = await self.announce_everywhere(message.content, message.author.avatar.url)
            await ctx.send(content=f"The announcement have been sent to {len(messages_sent)} "
                                   f"out of {guild_numbers} guild(s).",
                           hidden=True)
        except NotFound:
            await ctx.send(content="Could not retrieve the message. Please ensure that you are sending "
                                   "the command from the same channel than the message.",
                           hidden=True)
        except Forbidden:
            await ctx.send(content="Could not retrieve the message. You don't have enough "
                                   "permissions to read the message.",
                           hidden=True)
        except HTTPException:
            await ctx.send(content="Could not retrieve the message. "
                                   "Http exception triggered, please contact the admins.",
                           hidden=True)

    async def announce_everywhere(self, content: str, image_url: str) -> [List[Message], int]:
        announce_render = AnnouncementEmbedRender(content=content,
                                                  image_url=image_url)
        announce_view = ViewWithHiddenData(puppet_bot=self.bot,
                                           elements_to_display=None,
                                           render=announce_render)
        return await announce_everywhere(self.bot, self.cogs_name, announce_view)


async def announce_everywhere(bot, cogs_name: str, view: ViewWithHiddenData) -> [List[Message], int]:
    guild_numbers = len(bot.guilds)
    messages_sent = []
    for guild in bot.guilds:
        restriction_model = Settings.get_or_none(guild_id=guild.id, cog=cogs_name)
        if restriction_model is not None:
            announcement_channel = guild.get_channel(restriction_model.channel_id_restriction)
            message_sent = await view.display_view(announcement_channel)
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


async def announce_in_guild(bot, cogs_name: str, view: ViewWithHiddenData, guild_id: int) -> bool:
    guild = bot.get_guild(guild_id)
    if guild is not None:
        restriction_model = Settings.get_or_none(guild_id=guild.id, cog=cogs_name)
        if restriction_model is not None:
            announcement_channel = guild.get_channel(restriction_model.channel_id_restriction)
            await view.display_view(announcement_channel)
            return True
        else:
            for member in guild.members:
                if not member.bot and member.guild_permissions.administrator:
                    await member.send(f"{constants.REPORT_EMOJI} An announcement regarding Puppet bot as been made"
                                      f" but you haven't set a channel to receive it. In order for "
                                      f"Puppet to work properly, please create a TextChannel on your discord to "
                                      f"ensure to receive the latest news. {constants.REPORT_EMOJI}")
    return False


def setup(bot):
    bot.add_cog(AnnouncementCogs(bot))
