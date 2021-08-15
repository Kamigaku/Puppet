from discordClient.bot.puppetBot import PuppetBot


class Puppet:

    def __init__(self, token):
        self.token = token
        self.bot = PuppetBot(commands_prefix="puppet_test ")
        self.bot.default_initialisation()

    def connectToServer(self):
        self.bot.run(self.token)

