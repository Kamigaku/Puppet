from playhouse.migrate import SqliteMigrator

from discordClient.dal import dbContext
from discordClient.model import Settings

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS restriction;")
dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS disablement;")
dbContext.DbContext().sqliteConnection.create_tables([Settings])
