from peewee import BooleanField, IntegerField
from playhouse.migrate import migrate, SqliteMigrator, TextField

from discordClient.dal import dbContext
from discordClient.model import CharactersOwnership

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

migrate(
    # migrator.add_column("character", "url_link", TextField(default="")),
    # migrator.add_column("charactersownership", "is_sold", BooleanField(default=False)),
    # migrator.add_column("charactersownership", "dropped_by", IntegerField(default="")),
    migrator.drop_column("trade", "confirmation_code")
)

# characterownerships = CharactersOwnership.select()
# for ownership in characterownerships:
#     ownership.dropped_by = ownership.discord_user_id
#     ownership.save()
