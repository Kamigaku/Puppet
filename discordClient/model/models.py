from playhouse.migrate import *

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


class Affiliation(Model):
    name = CharField()
    category = CharField()

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


class Report(Model):
    category = CharField()
    card_id = IntegerField()
    comment = TextField()
    reporter_user_id = IntegerField()
    has_been_treated = BooleanField(default=False)
    action_done = TextField(default="")

    class Meta:
        database = db


class Moderator(Model):
    discord_user_id = IntegerField()

    class Meta:
        database = db


db.create_tables([Character, Affiliation, CharacterAffiliation, Economy, CharactersOwnership, Booster, Report,
                  Moderator])
