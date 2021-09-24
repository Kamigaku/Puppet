from peewee import *

from discordClient.model.meta_model import BaseModel


class Character(BaseModel):
    name = CharField()
    description = TextField()
    category = CharField()
    image_link = TextField()
    description_size = IntegerField()
    page_id = IntegerField()
    rarity = IntegerField()
    url_link = TextField()
