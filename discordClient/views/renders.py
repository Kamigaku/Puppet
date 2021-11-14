import abc
from typing import Any, List

import discord.abc
from discord import Embed, User

from discordClient.helper import constants


class Fields:

    def __init__(self, title: str, data: Any, inline: bool = True):
        self.title = title
        self.data = data
        self.inline = inline


#################################
#          META CLASS           #
#################################


class Render(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def generate_render(self, **t):
        pass


class EmbedRender(Render, metaclass=abc.ABCMeta):

    def __init__(self, msg_content: str = None):
        self.msg_content = msg_content

    @abc.abstractmethod
    def generate_render(self, **t) -> Embed:
        raise NotImplementedError("The method 'generate_render' needs to be implemented.")

    def generate_content(self) -> str:
        return self.msg_content


#################################
#      MODEL RENDERERS          #
#################################

# Represent a list of characters on one embed
class CharacterListEmbedRender(EmbedRender):

    def __init__(self, msg_content: str = None, menu_title: str = None, owner: discord.User = None):
        super().__init__(msg_content)
        self.menu_title = menu_title
        self.owner = owner

    def generate_render(self, **t) -> Embed:
        # Retrieve variables
        data = t["data"]
        page = t["page"]
        starting_index = t["starting_index"]

        embed = Embed()

        # Title
        if self.menu_title is not None:
            embed.set_author(name=self.menu_title)

        description = ""
        iteration = 1
        for character in data:
            description += f"`{starting_index + iteration}`."
            description += f" {constants.RARITIES_EMOJI[character.rarity]} "
            description += f"** [{constants.RARITIES_LABELS[character.rarity]}] {character.name} **"
            if self.owner is not None:  # On vient afficher ici un petit coeur si le perso est dans les favoris
                if self.owner.id in [favorite.discord_user_id for favorite in character.favorited_by]:
                    description += f" {constants.HEART_EMOJI}"
            description += "\n"
            iteration += 1
            description += ", ".join([affiliation.affiliation_id.name for affiliation in character.affiliated_to])
            description += "\n"

        embed.description = description

        # Footer
        embed.set_footer(text=f"Page: {page + 1}")
        return embed


# Represent a single character on one embed
class CharacterEmbedRender(EmbedRender):

    def __init__(self, common_users: List[User], msg_content: str = None):
        super().__init__(msg_content)
        self.common_users = {user.id: user for user in common_users}

    def generate_render(self, **t) -> Embed:
        # Retrieve datas
        data = t["data"]

        # Description
        character_description = data.description[:255]
        if len(data.description) > 255:
            character_description = data.description[:255] + "..."

        embed = Embed(colour=constants.RARITIES_COLORS[data.rarity],
                      description=character_description)

        # Thumbnail
        embed.set_thumbnail(url=data.image_link)

        # Icon url
        icon_url = constants.RARITIES_URL.format(constants.RARITIES_HEXA[data.rarity])

        # Author
        if data.url_link is not None:
            embed.set_author(name=data.name, icon_url=icon_url, url=data.url_link)
        else:
            embed.set_author(name=data.name, icon_url=icon_url)

        # Footer
        footer_text = f"Rarity: {constants.RARITIES_LABELS[data.rarity]} | Affiliation(s): " \
                      f"{', '.join([affiliation.affiliation_id.name for affiliation in data.affiliated_to])}"
        embed.set_footer(text=footer_text,
                         icon_url=icon_url)

        # Fields
        # Owners
        if len(self.common_users) > 0:
            field_owners_name = "Owners"
            field_owners_value = {}
            for owner in data.owned_by:
                if not owner.is_sold:
                    owner_id = owner.discord_user_id
                    if owner_id in self.common_users:
                        common_user = self.common_users[owner_id]
                        if owner.discord_user_id not in field_owners_value:
                            field_owners_value[owner_id] = {}
                            field_owners_value[owner_id]["name"] = f"{common_user.name}#{common_user.discriminator}"
                            field_owners_value[owner_id]["occurrence"] = 0
                        field_owners_value[owner_id]["occurrence"] += 1
            if len(field_owners_value) > 0:
                embed.add_field(name=field_owners_name,
                                value="\n".join([
                                    f"{field_owners_value[f]['name']} (**x{field_owners_value[f]['occurrence']}**)"
                                    for f in field_owners_value]),
                                inline=True)

        # Favorites
        if len(self.common_users) > 0:
            field_favorite_name = f"{constants.HEART_EMOJI} Favorites"
            field_favorite_value = []
            for favorite in data.favorited_by:
                if (favorite.discord_user_id in self.common_users and
                        favorite.discord_user_id not in field_favorite_value):
                    common_user = self.common_users[favorite.discord_user_id]
                    field_favorite_value.append(f"{common_user.name}#{common_user.discriminator}")
            if len(field_favorite_value) > 0:
                embed.add_field(name=field_favorite_name,
                                value="\n".join(field_favorite_value),
                                inline=True)

        return embed


# Represent a single character on multiple embed
class CharactersEmbedRender(CharacterEmbedRender):

    def generate_render(self, **t) -> Embed:
        embed = super().generate_render(**t)

        # Retrieve variables
        page = t["page"]
        embed.set_footer(text=f"{embed.footer.text} | Page {page + 1}",
                         icon_url=embed.footer.icon_url)
        return embed


# Represent a single character ownership on one embed
class CharacterOwnershipEmbedRender(CharacterEmbedRender):

    def generate_render(self, **t) -> Embed:
        # Retrieve variables
        character_ownership = t["data"]
        t["data"] = t["data"].character_id
        embed = super().generate_render(**t)
        embed.set_footer(text=f"{embed.footer.text} | Ownership_id: {character_ownership.id}",
                         icon_url=embed.footer.icon_url)
        return embed


# Represent a single character ownership on multiple embed
class CharactersOwnershipEmbedRender(CharacterOwnershipEmbedRender):

    def generate_render(self, **t) -> Embed:
        # Retrieve variables
        page = t["page"]
        embed = super().generate_render(**t)
        embed.set_footer(text=f"{embed.footer.text} | Page: {page + 1}",
                         icon_url=embed.footer.icon_url)
        return embed


#################################
#          MUSEUM COGS          #
#################################


class MuseumCharacterListEmbedRender(CharacterListEmbedRender):

    def generate_render(self, **t) -> Embed:
        # Retrieve variables
        data = t["data"]

        embed = super().generate_render(**t)

        # Title
        # if self.menu_title is not None:
        #     embed.set_author(name=self.menu_title)

        # Overload description
        description = ""
        iteration = 1
        for character in data:
            description += f"`{iteration}`. {constants.RARITIES_EMOJI[character.rarity]} " \
                           f"** [{constants.RARITIES_LABELS[character.rarity]}] {character.name} **"
            if character.count > 1:
                description += f" (x{character.count})"
            description += "\n"
            iteration += 1
            description += ", ".join([affiliation.affiliation_id.name for affiliation in character.affiliated_to])
            description += "\n"

        embed.description = description

        return embed


#################################
#          TRADE COGS           #
#################################


class TradeRecapEmbedRender(EmbedRender):

    def __init__(self, applicant: User, recipient: User, menu_title: str = "Trade recap", msg_content: str = ""):
        super().__init__(msg_content=msg_content)
        self.applicant = applicant
        self.recipient = recipient
        self.menu_title = menu_title

    def generate_render(self, data: List[Fields] = None) -> Embed:
        embed = Embed()

        embed.set_author(name=f"{self.applicant.name}#{self.applicant.discriminator}",
                         icon_url=self.applicant.avatar_url)
        embed.set_thumbnail(url=self.recipient.avatar_url)
        embed.title = self.menu_title
        embed.description = f"This section list the cards that will be traded between {self.applicant.mention} and " \
                            f"{self.recipient.mention}."

        # Fields
        for field in data:
            if len(field.data.data) > 0:
                field_str = "\n".join([f"{constants.RARITIES_EMOJI[char.character_id.rarity]} "
                                       f"**[{constants.RARITIES_LABELS[char.character_id.rarity]}] "
                                       f"{char.character_id.name} **"
                                       for char in field.data.data])
            else:
                field_str = "No character selected for the trade."
            embed.add_field(name=field.title,
                            value=field_str,
                            inline=field.inline)

        return embed


class TradeCharactersListEmbedRender(EmbedRender):

    def __init__(self, menu_title: str, current_owner: User, msg_content: str = None):
        super().__init__(msg_content=msg_content)
        self.menu_title = menu_title
        self.current_owner = current_owner

    # def generate_render(self, data: List[CharactersOwnership] = None, offset: int = 0,
    #                     starting_index: int = 0) -> Embed:
    def generate_render(self, **t) -> Embed:
        # Retrieve variables
        data = t["data"]
        page = t["page"]

        embed = Embed()
        if self.menu_title is not None:
            embed.title = self.menu_title
        description = ""
        for element in data:
            description += f"{constants.RARITIES_EMOJI[element.character_id.rarity]} " \
                           f"**[{constants.RARITIES_LABELS[element.character_id.rarity]}] " \
                           f"{element.character_id.name}**"
            description += f"\n{element.affiliations}\n"
        embed.description = description
        embed.set_footer(text=f"Page {page + 1}")
        embed.set_author(name=f"{self.current_owner.name}#{self.current_owner.discriminator}",
                         icon_url=self.current_owner.avatar_url)
        return embed


#################################
#       ANNOUNCEMENT COGS       #
#################################

class AnnouncementEmbedRender(EmbedRender):

    def __init__(self, content: str, image_url: str = ""):
        super().__init__(msg_content=f"{constants.REPORT_EMOJI} **__Puppet announcement__** {constants.REPORT_EMOJI}")
        self.content = content
        self.image_url = image_url

    def generate_render(self, data: List[Fields] = None) -> Embed:
        embed = Embed()

        embed.set_author(name="Puppet announcement")
        embed.set_thumbnail(url=self.image_url)
        embed.description = f"{self.content}"
        return embed

