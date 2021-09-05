from discord import Embed
from peewee import *

from discordClient.helper import constants
from discordClient.model.meta_model import BaseModel
import discordClient.model as model


class Character(BaseModel):
    name = CharField()
    description = TextField()
    category = CharField()
    image_link = TextField()
    description_size = IntegerField()
    page_id = IntegerField()
    rarity = IntegerField()
    url_link = TextField()

    def generate_embed(self) -> Embed:
        # Description
        if len(self.description) > 255:
            character_description = self.description[:255] + "..."
        else:
            character_description = self.description

        embed = Embed(colour=constants.RARITIES_COLORS[self.rarity],
                      description=character_description)

        # Thumbnail
        embed.set_thumbnail(url=self.image_link)

        # Icon url
        icon_url = constants.RARITIES_URL.format(constants.RARITIES_HEXA[self.rarity])

        # Author
        embed.set_author(name=self.name, icon_url=icon_url, url=self.url_link)

        # Footer
        footer_text = f"Rarity: {constants.RARITIES_LABELS[self.rarity]}"
        affiliations = self.retrieve_affiliations()
        if affiliations:
            footer_text += f" | Affiliation(s): {', '.join(affiliations)}"
        footer_text += f" | Character_id: {self.get_id()}"
        embed.set_footer(text=footer_text,
                         icon_url=icon_url)
        return embed

    def retrieve_affiliations(self) -> list:
        affiliations = []
        for current_affiliation in (model.Affiliation.select()
                                                     .join(model.CharacterAffiliation)
                                                     .join(Character)
                                                     .where(model.CharacterAffiliation.character_id == self.get_id())
                                                     .group_by(model.Affiliation)):
            affiliations.append(current_affiliation.name)
        return affiliations
