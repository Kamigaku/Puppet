from peewee import DoesNotExist

from discord.ext.commands import slash_command, ApplicationCommandField, InteractionContext
from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Report, Moderator


class ReportCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "report")

    ################################
    #       COMMAND COGS           #
    ################################

    @slash_command(description="Report a card",
                   is_global=True)
    async def report(self,
                     ctx: InteractionContext,
                     category: str = ApplicationCommandField(description="The category of the report",
                                                             required=True,
                                                             values={"Description incoherency": "description",
                                                                     "Invalid image": "image",
                                                                     "Invalid affiliation(s)": "affiliation",
                                                                     "Invalid name": "name",
                                                                     "Card incoherency": "card",
                                                                     "Other report": "other"}),
                     card_id: int = ApplicationCommandField(description="The id of the card to report",
                                                            required=True),
                     comment: str = ApplicationCommandField(description="Description of the report",
                                                            required=True)):
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

    @slash_command(description="Fix a report",
                   is_global=True)
    async def report_fix(self,
                         ctx: InteractionContext,
                         report_id: int = ApplicationCommandField(description="The id of the report to fix",
                                                                  required=True),
                         report_fix: str = ApplicationCommandField(description="The action done by the moderator to "
                                                                               "fix the issue",
                                                                   required=True)):
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


def setup(bot):
    bot.add_cog(ReportCogs(bot))
