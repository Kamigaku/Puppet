from peewee import IntegerField, BooleanField, DateTimeField
from playhouse.postgres_ext import DateTimeTZField

from discordClient.model.meta_model import BaseModel


class Event(BaseModel):
    type = IntegerField()  # 0: giveaway card
    target = IntegerField()  # Peut prendre deux valeurs: -1 si c'est un événement global ou l'id de la guild
    duration = IntegerField()  # Durée en secondes
    start_time = DateTimeField()  # Date de début de l'event
    format = IntegerField()  # (A CONFIRMER) Format de l'event: 0: random, 1: premier arrivé, 2: enchere
    status = IntegerField()  # 0: planifié, 1: en cours, 2: terminé, 3: annulé
    started_by = IntegerField(default=None, null=True)  # match the id of the creator
