from playhouse.migrate import SqliteMigrator, migrate

from discordClient.dal import dbContext
from discordClient.model import Settings, Event, EventParticipants
from discordClient.model.jointure_tables import EventRewards

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS restriction;")
dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS disablement;")
dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS event;")
dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS eventparticipants;")
dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS eventrewards;")
dbContext.DbContext().sqliteConnection.create_tables([Settings, Event, EventParticipants, EventRewards])

migrate(
    migrator.drop_column("charactersownership", "message_id")
)
