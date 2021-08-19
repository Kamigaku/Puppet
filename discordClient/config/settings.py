import configparser
from discordClient.dal import dbContext


def load_config():
    tempConfiguration = configparser.ConfigParser()
    tempConfiguration.read("config.ini")
    return tempConfiguration


configurationFile = load_config()
dbContext = dbContext.DbContext()
print(configurationFile.sections())
