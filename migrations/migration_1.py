from playhouse.migrate import *

from discordClient.dal import dbContext

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

migrate(
    migrator.add_column("affiliation", "category", CharField(default="Disney"))
)
