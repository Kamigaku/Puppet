import re
import asyncio

from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import Bot


class BaseCogs(commands.Cog):

    def __init__(self, bot: Bot, name):
        self.bot = bot
        self.cogs_name = name
        self.locked_message = {}

    def register_locked_message(self, message_id: int):
        if message_id not in self.locked_message:
            self.locked_message[message_id] = {}
            self.locked_message[message_id] = {
                "lock": asyncio.Lock(),
                "users": 0
            }
        self.locked_message[message_id]["users"] += 1
        self.bot.logger.info(f"registered message id {message_id}")

    def unregister_locked_message(self, message_id: int):
        if message_id in self.locked_message:
            self.locked_message[message_id]["users"] -= 1
            self.bot.logger.info(f"unregistered message id {message_id}")
            if self.locked_message[message_id]["users"] <= 0:
                del(self.locked_message[message_id])
                self.bot.logger.info(f"delete lock on message id {message_id}")

    async def retrieve_member(self, discord_user_id: int):
        discord_user = self.bot.get_user(discord_user_id)
        if discord_user is None:
            discord_user = await self.bot.fetch_user(discord_user_id)
        return discord_user

    def retrieve_from_embed(self, embeds: Embed, pattern: str):
        if embeds is not None and len(embeds) > 0:
            for embed in embeds:
                if embed.footer is not None:
                    regex_result = re.search(pattern=pattern, string=embed.footer.text)
                    if regex_result:
                        return regex_result.group(1)
        return ""
