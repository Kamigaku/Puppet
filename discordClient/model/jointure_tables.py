from peewee import *

from discordClient.model import Economy, Affiliation, Character
from discordClient.model.meta_model import BaseModel


class CharacterAffiliation(BaseModel):
    character_id = ForeignKeyField(Character, backref='rowid')
    affiliation_id = ForeignKeyField(Affiliation, backref='rowid')


class CharactersOwnership(BaseModel):

    discord_user_id = IntegerField()
    character_id = ForeignKeyField(Character, backref='rowid')
    message_id = IntegerField()
    is_sold = BooleanField(default=False)
    dropped_by = IntegerField(default=discord_user_id)

    def __repr__(self):
        return self.generate_embed()

    def generate_embed(self):
        character_owned = Character.get_by_id(self.character_id)
        character_embed = character_owned.generate_embed()
        footer_proxy = character_embed.footer
        character_embed.set_footer(text=f"{footer_proxy.text} | Ownership_id: {self.get_id()}",
                                   icon_url=footer_proxy.icon_url)
        return character_embed

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

