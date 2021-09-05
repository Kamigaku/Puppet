from peewee import *

from discordClient.model.meta_model import BaseModel


class Moderator(BaseModel):
    discord_user_id = IntegerField()
