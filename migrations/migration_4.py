from playhouse.migrate import SqliteMigrator

from discordClient.dal import dbContext
from discordClient.model import Restriction

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

dbContext.DbContext().sqliteConnection.create_tables([Restriction])
