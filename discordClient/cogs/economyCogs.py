from discord.ext import tasks
from discord.user import User
from discord import Status
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Economy


class EconomyCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "economy")
        self.distribute_salary.start()

    @cog_ext.cog_slash(name="give",
                       description="Send a specified amount of money to a desired user.",
                       options=[
                           create_option(
                               name="discord_user",
                               description="Specify the user that will receive the money",
                               option_type=SlashCommandOptionType.USER,
                               required=True
                           ),
                           create_option(
                               name="amount",
                               description="Specify an amount of money you want to give.",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True
                           )
                       ])
    async def give_money(self, ctx: SlashContext, discord_user: User, amount: int):
        if amount > 0:
            economy_model, model_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            if economy_model.give_money(discord_user.id, amount):
                content_to_sender = f"You have given {amount} {constants.COIN_NAME} to " \
                                    f"{discord_user.name}#{discord_user.discriminator}"
                await discord_user.send(f"You have been given {amount} {constants.COIN_NAME} from "
                                        f"{ctx.author.name}#{ctx.author.discriminator}")
            else:
                content_to_sender = f"You wanted to give {amount} {constants.COIN_NAME} but you don't have enough."
        else:
            content_to_sender = "You cannot give a negative number."
        await ctx.send(content=content_to_sender, hidden=True)

    @cog_ext.cog_slash(name="check",
                       description="Check the amount of money in your wallet or in the wallet of someone else",
                       options=[
                           create_option(
                               name="user",
                               description="The user to check",
                               option_type=SlashCommandOptionType.USER,
                               required=False
                           )
                       ])
    async def check_wallet(self, ctx: SlashContext, user: User = None):
        if user is None:
            user_model, user_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            content = f"You currently have {user_model.amount} {constants.COIN_NAME}."
        else:
            user_model, user_created = Economy.get_or_create(discord_user_id=user.id)
            content = f"The user {user.name}#{user.discriminator} currently have " \
                      f"{user_model.amount} {constants.COIN_NAME}."
        await ctx.send(content=content, hidden=True)

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
