from discordClient.bot.puppetBot import PuppetBot
from discordClient.helper import constants


class Puppet:

    def __init__(self, token):
        self.token = token
        self.bot = PuppetBot(commands_prefix=f"{constants.BOT_PREFIX} ")
        self.bot.default_initialisation()

    def connectToServer(self):
        self.bot.run(self.token)

