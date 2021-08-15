from discord.ext import tasks, commands
from discord.user import User
from discord import Status
from discordClient.cogs.abstract import baseCogs
from discordClient.model.models import *


class EconomyCogs(baseCogs.BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "economy")
        self.distribute_salary.start()

    @commands.command(name="give")
    async def give_money(self, ctx: Context, discord_user: User, amount_to_add: int):
        if amount_to_add > 0:
            if check_enough_amount(ctx.author.id, amount_to_add):
                await add_amount(discord_user, amount_to_add)
                await add_amount(ctx.author, -amount_to_add)
            else:
                await ctx.author.send("You wanted to give {} biteCoin but you don't have enough.".format(amount_to_add))
        else:
            await ctx.author.send("You cannot give a negative number.")

    @commands.command(name="check")
    async def check_wallet(self, ctx: Context):
        if ctx.guild is not None:
            await ctx.message.delete()
        user_model, user_created = Economy.get_or_create(discord_user_id=ctx.author.id)
        await ctx.author.send("You currently have {} biteCoin.".format(user_model.amount))

    @tasks.loop(minutes=10)
    async def distribute_salary(self):
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
                    if member.voice is not None:
                        amount *= 2
                    await add_amount(member, amount, False)


def setup(client):
    client.add_cog(EconomyCogs(client))


async def add_amount(discord_user: User, amount_to_add: int, send_message: bool = True):
    user_model, user_created = Economy.get_or_create(discord_user_id=discord_user.id)
    user_model.amount += amount_to_add
    user_model.save()
    if send_message:
        if amount_to_add > 0:
            await discord_user.send("You have been given {} biteCoin!".format(amount_to_add))
        else:
            await discord_user.send("You have given {} biteCoin!".format(amount_to_add * -1))


def check_enough_amount(discord_id: int, amount_to_check: int):
    user_model, user_created = Economy.get_or_create(discord_user_id=discord_id)
    return user_model.amount >= amount_to_check
