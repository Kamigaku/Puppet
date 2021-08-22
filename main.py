from discordClient import puppet
from discordClient.config import settings


def mainProcess():
    bot = puppet.Puppet(settings.configurationFile["KEYS"]["ApiKey"])
    bot.connectToServer()


if __name__ == '__main__':
    mainProcess()
