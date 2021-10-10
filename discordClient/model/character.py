from peewee import *

from discordClient.helper import constants
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

    def __str__(self):
        return f"{constants.RARITIES_EMOJI[self.rarity]} {self.name}"
