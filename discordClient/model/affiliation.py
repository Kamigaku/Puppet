from peewee import *

from discordClient.model import BaseModel


class Affiliation(BaseModel):
    name = CharField()
    category = CharField()
