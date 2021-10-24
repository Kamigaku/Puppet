from discord.ext import commands


class BaseCogs(commands.Cog):

    def __init__(self, bot, name: str):
        self.bot = bot
        self.cogs_name = name
        self.locked_message = {}

    async def retrieve_member(self, discord_user_id: int):
        discord_user = self.bot.get_user(discord_user_id)
        if discord_user is None:
            discord_user = await self.bot.fetch_user(discord_user_id)
        return discord_user
