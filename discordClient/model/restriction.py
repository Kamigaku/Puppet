from peewee import *

from discordClient.model.meta_model import BaseModel


class Restriction(BaseModel):
    guild_id = IntegerField()
    channel_id = IntegerField()
    cog = TextField()