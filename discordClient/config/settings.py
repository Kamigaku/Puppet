import configparser
from discordClient.dal import dbContext

def saveConfig():
    with open("config.ini", "w") as f:
        configurationFile.write(f)

def loadConfig():
    tempConfiguration = configparser.ConfigParser()
    tempConfiguration.read("config.ini")
    return tempConfiguration


configurationFile = loadConfig()
dbContext = dbContext.DbContext()
print(configurationFile.sections())
