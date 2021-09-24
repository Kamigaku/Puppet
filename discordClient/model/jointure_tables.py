from peewee import *

from discordClient.model import Economy, Affiliation, Character
from discordClient.model.meta_model import BaseModel


class CharacterAffiliation(BaseModel):
    character_id = ForeignKeyField(Character, backref='affiliated_to')
    affiliation_id = ForeignKeyField(Affiliation, backref='affiliated_by')


class CharactersOwnership(BaseModel):
    discord_user_id = IntegerField()
    character_id = ForeignKeyField(Character, backref='owned_by')
    message_id = IntegerField()
    is_sold = BooleanField(default=False)
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

