from discordClient.bot import PuppetBot


class Puppet:

    def __init__(self, token, prefix):
        self.token = token
        self.bot = PuppetBot(commands_prefix=f"{prefix}")
        self.bot.default_initialisation()

    def connect_to_server(self):
        self.bot.run(self.token)
