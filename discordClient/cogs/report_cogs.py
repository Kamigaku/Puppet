from discord import RawReactionActionEvent
from discord import Embed, Colour
from discord.ext import commands
from discord.ext.commands import Context
from peewee import DoesNotExist
from discordClient.cogs.abstract import baseCogs
from discordClient.cogs import cardCogs
from discordClient.helper import constants
from discordClient.model.models import Character, Report, Moderator


class ReportCogs(baseCogs.BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "report")

    def retrieve_character_id(self, embeds: Embed) -> int:
        return int(self.retrieve_from_embed(embeds, "Character_id: (\d+)"))

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("report")
    async def report(self, ctx: Context, category: str, card_id: int, comment: str):
        Report.create(category=category, card_id=card_id, comment=comment, reporter_user_id=ctx.author.id)
        await ctx.author.send(f"{constants.CHECK_EMOJI} Your report has been sent.")

    @commands.command("report_display")
    async def report_display(self, ctx: Context):
        try:
            Moderator.get(Moderator.discord_user_id == ctx.author.id)
            reports = Report.select().where(Report.has_been_treated == False)
            for report in reports:
                author = await self.retrieve_member(report.reporter_user_id)
                concerned_character = Character.get(Character.id == report.card_id)
                report_embed = Embed()
                report_embed.set_author(name=f"{concerned_character.name} - Category: {report.category}")
                report_embed.title = f"{constants.WARNING_EMOJI} Report"
                report_embed.description = report.comment
                report_embed.colour = Colour(0xFF0000)
                report_embed.add_field(name="__Report fixing__",
                                       value=f"{self.bot.command_prefix}report_fix {report.id} \"[YOUR COMMENT]\"")
                report_embed.set_footer(text=f"Report done by {author.name} | "
                                             f"Character_id: {report.card_id} | "
                                             f"Puppet_id: {constants.PUPPET_IDS['REPORT_COGS_DETAIL']}")
                msg = await ctx.author.send(embed=report_embed)
                await msg.add_reaction(constants.DETAILS_EMOJI)
        except DoesNotExist:
            await ctx.author.send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
                                  f"functionality. {constants.WARNING_EMOJI}")

    @commands.command("report_fix")
    async def report_fix(self, ctx: Context, report_id: int, report_fix: str):
        try:
            Moderator.get(Moderator.discord_user_id == ctx.author.id)
            report = Report.get(Report.id == report_id)
            report.has_been_treated = True
            report.action_done = report_fix
            report.save()
        except DoesNotExist:
            await ctx.author.send(f"{constants.WARNING_EMOJI} You are not a moderator, you cannot access this "
                                  f"functionality. {constants.WARNING_EMOJI}")

    ################################
    #       ERRORS HANDLING        #
    ################################

    @report.error
    async def on_report_error(self, ctx: Context, error):
        await ctx.author.send(f"{constants.WARNING_EMOJI} Your report is incoherent, you need to send a report that "
                              f"follow the pattern: **\"{self.bot.command_prefix}report [CATEGORY] [CARD_ID] "
                              f"[COMMENT]\"** {constants.WARNING_EMOJI}.")

    @report_fix.error
    async def on_report_fix_error(self, ctx: Context, error):
        await ctx.author.send(f"{constants.WARNING_EMOJI} Your report fix is incoherent, you need to send a fix that "
                              f"follow the pattern: **\"{self.bot.command_prefix}report_fix [REPORT_ID] "
                              f"[COMMENT]\"** {constants.WARNING_EMOJI}.")

    ################################
    #       LISTENER COGS          #
    ################################

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        ####
        # Init actions
        if self.bot.user.id == payload.user_id:  # We avoid to react to the current bot reactions
            return

        # We avoid situation that doesn't matter
        user_that_reacted = await self.retrieve_member(payload.user_id)
        if user_that_reacted.bot is True or payload.event_type != "REACTION_ADD":
            return

        # Variables that are needed to determine path
        origin_message = await self.retrieve_message(payload.channel_id, payload.message_id)
        puppet_id = self.retrieve_puppet_id(origin_message.embeds)

        # End Init Actions
        ####

        # We filter only on what we seek
        if puppet_id == constants.PUPPET_IDS["CARD_COGS_BUY"]:
            if str(payload.emoji) == constants.REPORT_EMOJI:  # Signal the card
                character_id = self.retrieve_character_id(origin_message.embeds)
                character = Character.get(Character.id == character_id)
                embed = Embed()
                embed.title = f"{constants.REPORT_EMOJI} Report a card"
                embed.colour = Colour(0xFF0000)
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
                                value=f"{self.bot.command_prefix}report description {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                embed.add_field(name="__Invalid image__",
                                value=f"{self.bot.command_prefix}report image {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                embed.add_field(name="__Invalid affiliation(s)__",
                                value=f"{self.bot.command_prefix}report affiliation {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                embed.add_field(name="__Invalid name__",
                                value=f"{self.bot.command_prefix}report name {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                embed.add_field(name="__Card incoherency__",
                                value=f"{self.bot.command_prefix}report card {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                embed.add_field(name="__Other report__",
                                value=f"{self.bot.command_prefix}report other {character_id} **\"[YOUR COMMENT]\"**",
                                inline=False)
                await user_that_reacted.send(embed=embed)
        elif puppet_id == constants.PUPPET_IDS["REPORT_COGS_DETAIL"]:
            if str(payload.emoji) == constants.DETAILS_EMOJI:
                character_id = self.retrieve_character_id(origin_message.embeds)
                character = Character.get(Character.id == character_id)
                character_embed = cardCogs.generate_embed_character(character)
                await user_that_reacted.send(embed=character_embed, delete_after=300)