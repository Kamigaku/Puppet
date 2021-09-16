from discord.ext import tasks, commands
from discord.ext.commands import Context
from discord.user import User
from discord import Status
from discordClient.cogs.abstract import baseCogs
from discordClient.helper import constants
from discordClient.model import Economy


class EconomyCogs(baseCogs.BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "economy")
        self.distribute_salary.start()

    @commands.command(name="give")
    async def give_money(self, ctx: Context, discord_user: User, amount: int):
        if amount > 0:
            economy_model, model_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            if economy_model.give_money(discord_user, amount):
                await ctx.author.send(f"You have given {amount} {constants.COIN_NAME} to "
                                      f"{discord_user.name}#{discord_user.discriminator}")
                await discord_user.send(f"You have been given {amount} {constants.COIN_NAME} from "
                                        f"{ctx.author.name}#{ctx.author.discriminator}")
            else:
                await ctx.author.send(f"You wanted to give {amount} {constants.COIN_NAME} but you don't have enough.")
        else:
            await ctx.author.send("You cannot give a negative number.")

    @commands.command(name="check")
    async def check_wallet(self, ctx: Context):
        if ctx.guild is not None:
            await ctx.message.delete()
        user_model, user_created = Economy.get_or_create(discord_user_id=ctx.author.id)
        await ctx.author.send(str(user_model))

    @tasks.loop(minutes=10)
    async def distribute_salary(self):
        self.bot.logger.info("Starting salary distribution.")
        fetched_ids = []
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id not in fetched_ids:
                    fetched_ids.append(member.id)
                    amount = 0
                    if member.status == Status.online:
                        amount = 2
                    elif member.status == Status.idle or member.status == Status.do_not_disturb:
                        amount = 1
                    if (member.voice is not None and
                       not member.voice.afk and
                       not member.voice.self_deaf and
                       not member.voice.self_mute):
                        amount *= 2
                    economy_model, model_created = Economy.get_or_create(discord_user_id=member.id)
                    economy_model.add_amount(amount)
        self.bot.logger.info("End of salary distribution.")
