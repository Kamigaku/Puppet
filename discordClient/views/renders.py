import abc
from typing import Any, List

from discord import Embed, User

from discordClient.helper import constants
from discordClient.model import Character, CharactersOwnership


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
    def generate_render(self):
        pass


class EmbedRender(Render, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, msg_content: str = None):
        self.msg_content = msg_content

    @abc.abstractmethod
    def generate_render(self, data: Any = None) -> Embed:
        pass

    def generate_content(self) -> str:
        return self.msg_content


class ListEmbedRender(EmbedRender, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def generate_render(self, data: Any = None, offset: int = 0, starting_index: int = 0) -> Embed:
        pass

#################################
#          RENDERERS            #
#################################


class CharacterEmbedRender(ListEmbedRender):

    def __init__(self, msg_content: str = None):
        super().__init__(msg_content)

    def generate_render(self, data: List[Character], offset: int = 0, starting_index: int = 0) -> Embed:
        # Description
        if len(data.description) > 255:
            character_description = data.description[:255] + "..."
        else:
            character_description = data.description

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
                      f"{', '.join([affiliation.affiliation_id.name for affiliation in data.affiliated_to])} | " \
                      f"Page: {offset + 1}"
        embed.set_footer(text=footer_text,
                         icon_url=icon_url)
        return embed


class CharacterListEmbedRender(ListEmbedRender):

    def __init__(self, msg_content: str = None, menu_title: str = None):
        super().__init__(msg_content)
        self.menu_title = menu_title

    def generate_render(self, data: List[Character], offset: int = 0, starting_index: int = 0) -> Embed:
        embed = Embed()

        # Title
        if self.menu_title is not None:
            embed.set_author(name=self.menu_title)

        description = ""
        iteration = 1
        for character in data:
            description += f"`{starting_index + iteration}`. {constants.RARITIES_EMOJI[character.rarity]} " \
                           f"** [{constants.RARITIES_LABELS[character.rarity]}] {character.name} **\n"
            iteration += 1
            description += ", ".join([affiliation.affiliation_id.name for affiliation in character.affiliated_to])
            description += "\n"

        embed.description = description

        # Footer
        embed.set_footer(text=f"Page: {offset+1}")
        return embed


class NumbersListEmbedRender(ListEmbedRender):

    def __init__(self, menu_title: str = None):
        super().__init__()
        self.menu_title = menu_title

    def generate_render(self, data: List[str] = None, offset: int = 0, starting_index: int = 0) -> Embed:
        embed = Embed()
        if self.menu_title is not None:
            embed.title = self.menu_title
        iteration = 1
        description = ""
        for element in data:
            description += f"{constants.NUMBER_EMOJIS[iteration]} • {element}\n"
            iteration += 1
        embed.description = description
        embed.set_footer(text=f"Page {offset + 1}")
        return embed


class AllAndNumbersListEmbedRender(NumbersListEmbedRender):

    def generate_render(self, data: List[str] = None, offset: int = 0, starting_index: int = 0) -> Embed:
        embed = super().generate_render(data=data,
                                        offset=offset,
                                        starting_index=starting_index)
        embed.description += f"{constants.ASTERISK_EMOJI} All\n"
        return embed

#################################
#          CARD COGS            #
#################################


class OwnersCharacterListEmbedRender(CharacterEmbedRender):

    def __init__(self, owners: List[Fields], msg_content: str = None):
        super().__init__(msg_content)
        self.owners = owners

    def generate_render(self, data: List[Character], offset: int = 0, starting_index: int = 0) -> Embed:
        embed = super().generate_render(data, offset, starting_index)
        embed.add_field(name=self.owners[offset].title,
                        value=self.owners[offset].data,
                        inline=self.owners[offset].inline)
        return embed


#################################
#          MUSEUM COGS          #
#################################


class MuseumCharacterListEmbedRender(ListEmbedRender):

    def __init__(self, msg_content: str = None):
        super().__init__(msg_content)

    def generate_render(self, data: List[Character], offset: int = 0, starting_index: int = 0) -> Embed:
        embed = Embed()

        # Title
        # if self.menu_title is not None:
        #     embed.set_author(name=self.menu_title)

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

        # Footer
        embed.set_footer(text=f"Page: {offset+1}")
        return embed


class MuseumCharacterOwnershipListEmbedRender(ListEmbedRender):

    def __init__(self):
        super().__init__()

    def generate_render(self, data: CharactersOwnership, offset: int = 0, starting_index: int = 0) -> Embed:
        character = data.character_id
        # Description
        if len(character.description) > 255:
            character_description = character.description[:255] + "..."
        else:
            character_description = character.description

        embed = Embed(colour=constants.RARITIES_COLORS[character.rarity],
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

        # Footer
        footer_text = f"Rarity: {constants.RARITIES_LABELS[character.rarity]} | Affiliation(s): " \
                      f"{', '.join([affiliation.affiliation_id.name for affiliation in character.affiliated_to])} | " \
                      f"Ownership id: {data.id} | Page: {offset + 1}"
        embed.set_footer(text=footer_text,
                         icon_url=icon_url)
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

    def generate_render(self, data: List[Fields]) -> Embed:
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


class TradeNumbersListEmbedRender(NumbersListEmbedRender):

    def __init__(self, menu_title: str, current_owner: User):
        super().__init__(menu_title)
        self.current_owner = current_owner

    def generate_render(self, data: List[str] = None, offset: int = 0, starting_index: int = 0) -> Embed:
        embed = super().generate_render(data, offset, starting_index)
        embed.set_author(name=f"{self.current_owner.name}#{self.current_owner.discriminator}",
                         icon_url=self.current_owner.avatar_url)
        embed.title = "Summary of owned characters"
        return embed
