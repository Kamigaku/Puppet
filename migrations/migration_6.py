from peewee import IntegerField, DateTimeField
from playhouse.migrate import SqliteMigrator, migrate

from discordClient.dal import dbContext

migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

dbContext.DbContext().sqliteConnection.execute_sql("DROP TABLE IF EXISTS eventparticipants;")

migrate(
    migrator.add_column("event", "guild_id", IntegerField(default=None, null=True)),
    migrator.add_column("event", "number_of_winner", IntegerField(default=1)),
    migrator.add_column("event", "end_time", DateTimeField(null=True)),
    migrator.add_column("event", "event_id", IntegerField(null=True)),
    migrator.drop_column("event", "target"),
    migrator.drop_column("event", "duration"),
    migrator.drop_column("event", "started_by"),
    migrator.drop_column("event", "start_time")
)
