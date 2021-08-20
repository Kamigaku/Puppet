from discord.ext import commands
from discord import Intents

from discordClient.cogs.cardCogs import CardCogs
from discordClient.cogs.economyCogs import EconomyCogs
from discordClient.cogs.museumCogs import MuseumCogs
from discordClient.cogs.report_cogs import ReportCogs


class PuppetBot(commands.Bot):

    def __init__(self, commands_prefix: str):
        intents = Intents.default()
        intents.members = True
        intents.presences = True
        intents.reactions = True
        super().__init__(command_prefix=commands_prefix, intents=intents)

    def default_initialisation(self):
        self.add_cog(EconomyCogs(self))
        self.add_cog(CardCogs(self))
        self.add_cog(MuseumCogs(self))
        self.add_cog(ReportCogs(self))
