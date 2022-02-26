from peewee import *

from discordClient.model import Economy, Affiliation, Character, Event
from discordClient.model.meta_model import BaseModel


class CharacterFavorites(BaseModel):
    character_id = ForeignKeyField(Character, backref='favorited_by')
    discord_user_id = IntegerField()


class CharacterAffiliation(BaseModel):
    character_id = ForeignKeyField(Character, backref='affiliated_to')
    affiliation_id = ForeignKeyField(Affiliation, backref='affiliated_by')


class CharactersOwnership(BaseModel):
    discord_user_id = IntegerField()
    character_id = ForeignKeyField(Character, backref='owned_by')
    is_sold = BooleanField(default=False)
    is_locked = BooleanField(default=False)
    dropped_by = IntegerField(default=discord_user_id)

    def sell(self) -> int:
        if not self.is_sold:
            character_model = Character.get_by_id(self.character_id)
            economy_model, user_created = Economy.get_or_create(discord_user_id=self.discord_user_id)
            economy_model.add_amount(character_model.rarity)
            self.is_sold = True
            self.save()
            return character_model.rarity
        return -1

    def trade_to(self, new_owner: int):
        if self.discord_user_id != new_owner:
            self.discord_user_id = new_owner
            self.save()

    def lock(self) -> bool:
        self.is_locked = not self.is_locked
        self.save()
        return self.is_locked

    def __str__(self):
        return f"{self.character_id}"


class EventRewards(BaseModel):
    event_id = ForeignKeyField(Event, backref='rewards')
    card_id = ForeignKeyField(Character, null=True)
    money_amount = IntegerField(null=True)
    booster_amount = IntegerField(null=True)

