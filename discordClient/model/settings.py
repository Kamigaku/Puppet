from peewee import *

from discordClient.model.meta_model import BaseModel


class Settings(BaseModel):
    guild_id = IntegerField()
    channel_id_restriction = IntegerField(default=None, null=True)
    cog = TextField()
    is_disabled = BooleanField(default=False)
