import re
from discord import RawReactionActionEvent, Embed, Message
from discord.ext import commands
from discord.ext.commands import Bot


class BaseCogs(commands.Cog):

    def __init__(self, bot: Bot, name):
        self.bot = bot
        self.cogs_name = name
        self.reactions_listener = []

    async def retrieve_member(self, discord_user_id: int):
        return await self.bot.fetch_user(discord_user_id)

    async def retrieve_message(self, channel_id: int, message_id: int):
        channel_retrieved = await self.bot.fetch_channel(channel_id)
        return await channel_retrieved.fetch_message(message_id)

    async def retrieve_origin_reply_message(self, message: Message):
        while message.reference is not None:
            message = await self.retrieve_message(message.reference.channel_id, message.reference.message_id)
        return message

    def retrieve_puppet_id(self, embeds: Embed) -> int:
        return int(self.retrieve_from_embed(embeds, "Puppet_id: (\d+)"))

    def retrieve_from_embed(self, embeds: Embed, pattern: str):
        if embeds is not None and len(embeds) > 0:
            for embed in embeds:
                if embed.footer is not None:
                    regex_result = re.search(pattern=pattern, string=embed.footer.text)
                    if regex_result:
                        return regex_result.group(1)
        return ""

    ################################
    #       LISTENER COGS          #
    ################################

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        message_id = payload.message_id
        user_id = payload.user_id
        for reaction_listener in self.reactions_listener:
            if reaction_listener.message_id == message_id and reaction_listener.author_id == user_id:
                reaction_listener.callback(payload)
            pass