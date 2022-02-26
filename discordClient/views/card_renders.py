import typing

from discord import Embed, Colour
from discordClient.helper import constants

from discordClient.views import EmbedRender


class WishlistRender(EmbedRender):

    def __init__(self):
        super().__init__(msg_content="Displaying your wishlist")

    def generate_render(self, **t) -> Embed:
        # Retrieve datas
        character_favorite = t["data"]
        page = t["page"]
        character = character_favorite.character_id

        # Description
        character_description = character.description[:255]
        if len(character.description) > 255:
            character_description = character.description[:255] + "..."

        embed = Embed(colour=Colour(constants.RARITIES_COLORS[character.rarity]),
                      description=character_description)

        # Thumbnail
        embed.set_thumbnail(url=character.image_link)

        # Icon url
        icon_url = constants.RARITIES_URL.format(constants.RARITIES_HEXA[character.rarity])

        # Author
        if character.url_link is not None:
            embed.set_author(name=character.name, icon_url=icon_url, url=character.url_link)
        else:
            embed.set_author(name=character.name, icon_url=icon_url)

        # Users that can trade
        owners: typing.Dict = {}
        if isinstance(character_favorite.owners, str):
            for owner in character_favorite.owners.split(","):
                if owner not in owners:
                    owners[owner] = 0
                owners[owner] += 1
        else:
            owners[str(character_favorite.owners)] = 1
        embed.add_field(name="Tradable users",
                        value="\n".join([f"- <@{o}> (x{q})" for o, q in owners.items()]),
                        inline=True)

        # Footer
        # footer_text = f"Rarity: {constants.RARITIES_LABELS[character.rarity]} | Affiliation(s): " \
        #               f"{', '.join([affiliation.affiliation_id.name for affiliation in character.affiliated_to])}"
        footer_text = f"Rarity: {constants.RARITIES_LABELS[character.rarity]} | Affiliation(s): " \
                      f"{character_favorite.aff} | Page {page + 1}"
        embed.set_footer(text=footer_text,
                         icon_url=icon_url)

        return embed
