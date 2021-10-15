from peewee import BooleanField
from playhouse.migrate import migrate, SqliteMigrator

from discordClient.dal import dbContext
from discordClient.model import CharacterFavorites

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

dbContext.DbContext().sqliteConnection.create_tables([CharacterFavorites])

migrate(
    migrator.add_column("charactersownership", "is_locked", BooleanField(default=False))
)
