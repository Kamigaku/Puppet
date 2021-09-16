from peewee import *

from discordClient.model.meta_model import BaseModel


class Booster(BaseModel):
    name = CharField()
    price = IntegerField()
    rarities = CharField()
    collection = CharField()
