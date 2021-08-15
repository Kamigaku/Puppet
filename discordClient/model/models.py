from peewee import *
from playhouse.migrate import *
from playhouse.sqlite_ext import RowIDField

from discordClient.dal import dbContext

db = dbContext.DbContext().sqliteConnection


class Character(Model):
    name = CharField()
    description = TextField()
    category = CharField()
    image_link = TextField()
    description_size = IntegerField()
    page_id = IntegerField()
    rarity = IntegerField()

    class Meta:
        database = db


class Feature(Model):
    name = CharField()
    type = CharField()

    class Meta:
        database = db


class Affiliation(Model):
    name = CharField()

    class Meta:
        database = db


class Rating(Model):
    author = CharField()
    element_id = CharField()
    comment = CharField()
    type = CharField()
    rate = FloatField()

    class Meta:
        database = db


class Event(Model):
    author = CharField()
    date = CharField()
    comment = CharField()

    class Meta:
        database = db


class CharacterOccurrence(Model):
    character_id = ForeignKeyField(Character, backref='rowid')
    feature_id = ForeignKeyField(Feature, backref='rowid')

    class Meta:
        database = db


class CharacterAffiliation(Model):
    character_id = ForeignKeyField(Character, backref='rowid')
    affiliation_id = ForeignKeyField(Affiliation, backref='rowid')

    class Meta:
        database = db


class Economy(Model):
    discord_user_id = IntegerField()
    amount = IntegerField(default=0)

    class Meta:
        database = db


class CharactersOwnership(Model):
    discord_user_id = IntegerField()
    character_id = ForeignKeyField(Character, backref='rowid')
    message_id = IntegerField()

    class Meta:
        database = db


class Booster(Model):
    name = CharField()
    price = IntegerField()
    rarities = CharField()
    collection = CharField()

    class Meta:
        database = db


db.create_tables([Character, Feature, Affiliation, CharacterAffiliation, CharacterOccurrence, Event, Rating, Economy,
                  CharactersOwnership])
migrator = SqliteMigrator(dbContext.DbContext().sqliteConnection)

migrate(
    #migrator.drop_column("charactersownership", "amount"),
    #migrator.add_column("charactersownership", "message_id", IntegerField(default=-1))
)
