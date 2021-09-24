from discordClient.cogs.abstract import BaseCogs


class AssignableCogs(BaseCogs):

    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.channel_id = ""

    async def assign_channel(self, ctx, channel_id: str):
        self.channel_id = channel_id
        await ctx.message.delete()
