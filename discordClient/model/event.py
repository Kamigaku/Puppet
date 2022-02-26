from peewee import IntegerField, DateTimeField

from discordClient.model.meta_model import BaseModel


class Event(BaseModel):
    type = IntegerField()  # 0: giveaway card
    end_time = DateTimeField()  # Date de fin de l'event
    format = IntegerField()  # (A CONFIRMER) Format de l'event: 0: random, 1: premier arrivé, 2: enchere
    status = IntegerField()  # 1: scheduled, 2: active, 3: completed, 4: canceled
    number_of_winner = IntegerField(default=1)  # nombre de gagnant
    guild_id = IntegerField(default=None)
    event_id = IntegerField(null=True)
