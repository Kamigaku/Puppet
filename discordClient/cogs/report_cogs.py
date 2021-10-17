from discord import User
from discord import Embed, Message
from peewee import DoesNotExist
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, create_choice

from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Character, Report, Moderator


class ReportCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "report")
        self.enable()

    def enable(self):
        # self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
        #                                           constants.REPORT_EMOJI,
        #                                           self.report_message,
        #                                           constants.PUPPET_IDS["CARD_COGS_BUY"]))
        # self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
        #                                           constants.DETAILS_EMOJI,
        #                                           self.report_details,
        #                                           constants.PUPPET_IDS["REPORT_COGS_DETAIL"]))
        pass

    def retrieve_character_id(self, embeds: Embed) -> int:
        return int(self.retrieve_from_embed(embeds, "Character_id: (\d+)"))

    ################################
    #       CALLBACKS              #
    ################################

    async def report_message(self, origin_message: Message, user_that_reacted: User):
        character_id = self.retrieve_character_id(origin_message.embeds)
        character = Character.get_by_id(character_id)
        embed = Embed()
        embed.title = f"{constants.REPORT_EMOJI} Report a card"
        embed.colour = 0xFF0000
        embed.description = f"Hello, you are on your way to report the card **{character.name}**.\n\n"
        embed.description += "Reporting a card means that the current card has something that you judge " \
                             "incoherent, invalid or maybe because the card should not exist.\n\n **__Please " \
                             "note that your report will be sent to a moderator that will review them in " \
                             "order to judge if they are valid or not. Do not add any personal datas or " \
                             "anything that could lead to a ban of the Puppet project.__**\n\n To be more " \
                             "precise on the category of your report, you will find below a list of commands " \
                             "that you can send to describe the type of report you want to do : "
        embed.set_thumbnail(url=character.image_link)
        embed.add_field(name="__Description incoherency__",
                        value=f"{constants.BOT_PREFIX} report description {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid image__",
                        value=f"{constants.BOT_PREFIX} report image {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid affiliation(s)__",
                        value=f"{constants.BOT_PREFIX} report affiliation {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid name__",
                        value=f"{constants.BOT_PREFIX} report name {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Card incoherency__",
                        value=f"{constants.BOT_PREFIX} report card {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Other report__",
                        value=f"{constants.BOT_PREFIX} report other {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        await user_that_reacted.send(embed=embed)

    async def report_details(self, origin_message: Message, user_that_reacted: User):
        character_id = self.retrieve_character_id(origin_message.embeds)
        character = Character.get_by_id(character_id)
        character_embed = character.generate_embed()
        await user_that_reacted.send(embed=character_embed, delete_after=300)

    ################################
    #       COMMAND COGS           #
    ################################

    @cog_ext.cog_slash(name="report",
                       description="Report a card ",
                       options=[
                           create_option(
                               name="category",
                               description="The category of the report",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                               choices=[
                                 create_choice(
                                   name="Description incoherency",
                                   value="description"
                                 ),
                                 create_choice(
                                   name="Invalid image",
                                   value="image"
                                 ),
                                 create_choice(
                                   name="Invalid affiliation(s)",
                                   value="affiliation"
                                 ),
                                 create_choice(
                                   name="Invalid name",
                                   value="name"
                                 ),
                                 create_choice(
                                   name="Card incoherency",
                                   value="card"
                                 ),
                                 create_choice(
                                   name="Other report",
                                   value="other"
                                 )
                               ]
                           ),
                           create_option(
                               name="card_id",
                               description="The id of the card to report",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True,
                           ),
                           create_option(
                               name="comment",
                               description="Description of the report",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           )
                       ])
    async def report(self, ctx: SlashContext, category: str, card_id: int, comment: str):
        Report.create(category=category, card_id=card_id, comment=comment, reporter_user_id=ctx.author.id)
        await ctx.send(f"{constants.CHECK_EMOJI} Your report has been sent.")

    # @commands.command("report_display")
    # async def report_display(self, ctx: Context):
    #     try:
    #         Moderator.get(Moderator.discord_user_id == ctx.author.id)
    #         reports = Report.select().where(Report.has_been_treated == False)
    #         for report in reports:
    #             author = await self.retrieve_member(report.reporter_user_id)
    #             report_embed = report.generate_embed()
    #             footer_proxy = report_embed.footer
    #             report_embed.set_footer(
    #                 text=f"Report done by {author.name}#{author.discriminator} | {footer_proxy.text} | "
    #                      f"Puppet_id: {constants.PUPPET_IDS['REPORT_COGS_DETAIL']}",
    #                 icon_url=footer_proxy.icon_url)
    #             msg = await ctx.author.send(embed=report_embed)
    #             await msg.add_reaction(constants.DETAILS_EMOJI)
    #     except DoesNotExist:
    #         await ctx.author.send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
    #                               f"functionality. {constants.WARNING_EMOJI}")

    @cog_ext.cog_slash(name="report_fix",
                       description="Report a card",
                       options=[
                           create_option(
                               name="report_id",
                               description="The id of the report to fix",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True,
                           ),
                           create_option(
                               name="report_fix",
                               description="The action done by the moderator to fix the issue",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           )
                       ])
    async def report_fix(self, ctx: SlashContext, report_id: int, report_fix: str):
        try:
            Moderator.get(Moderator.discord_user_id == ctx.author.id)
            report = Report.get_by_id(report_id)
            report.fix(report_fix)
            await ctx.send(f"{constants.CHECK_EMOJI} Your report fixing has been sent", hidden=True)
        except DoesNotExist:
            await ctx.send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
                           f"functionality. {constants.WARNING_EMOJI}", hidden=True)

    ################################
    #       ERRORS HANDLING        #
    ################################

    # @report.error
    # async def on_report_error(self, ctx: Context, error):
    #     await ctx.author.send(f"{constants.WARNING_EMOJI} Your report is incoherent, you need to send a report that "
    #                           f"follow the pattern: **\"{self.bot.command_prefix} report [CATEGORY] [CARD_ID] "
    #                           f"[COMMENT]\"** {constants.WARNING_EMOJI}.")
    #
    # @report_fix.error
    # async def on_report_fix_error(self, ctx: Context, error):
    #     await ctx.author.send(f"{constants.WARNING_EMOJI} Your report fix is incoherent, you need to send a fix that "
    #                           f"follow the pattern: **\"{self.bot.command_prefix} report_fix [REPORT_ID] "
    #                           f"[COMMENT]\"** {constants.WARNING_EMOJI}.")
