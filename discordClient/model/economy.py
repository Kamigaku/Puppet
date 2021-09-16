from peewee import *

from discordClient.helper import constants
from discordClient.model.meta_model import BaseModel


class Economy(BaseModel):
    discord_user_id = IntegerField()
    amount = IntegerField(default=0)

    def add_amount(self, amount: int) -> bool:
        self.amount += amount
        if self.amount < 0:
            return False
        self.save()
        return True

    def remove_amount(self, amount: int) -> bool:
        return self.add_amount(-amount)

    def give_money(self, discord_user_id: int, amount: int) -> bool:
        if amount > 0 and self.amount - amount > 0:
            economy_model, model_created = Economy.get_or_create(discord_user_id=discord_user_id)
            self.add_amount(-amount)
            economy_model.add_amount(amount)
            return True
        return False

    def __str__(self):
        return f"You currently have {self.amount} {constants.COIN_NAME}."
