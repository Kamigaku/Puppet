import typing

import discord
from discordClient.helper import constants
from discordClient.model import Affiliation

if typing.TYPE_CHECKING:
    from discordClient.cogs.museum_cogs import MuseumDataFilter


class RaritySelect(discord.ui.Select):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 on_change: typing.Callable = None):
        super().__init__(options=[discord.SelectOption(label=f"{constants.RARITIES_LABELS[index]}",
                                                       value=f"{index}",
                                                       emoji=f"{constants.RARITIES_EMOJI[index]}")
                                  for index in range(1, 7)],
                         placeholder="Select the rarity you want to apply",
                         custom_id="rarity_select",
                         max_values=6,
                         row=row,
                         disabled=disabled)
        self.on_change = on_change

    async def callback(self, interaction: discord.Interaction):  # TODO j'aime pas du tout ce qui est fait ici
        museum_filter = self.view.get_hidden_data()
        museum_filter.set_rarity(interaction.data['values'])
        if self.on_change is not None:
            await self.on_change(self, interaction)


class AffiliationSelect(discord.ui.Select):

    def __init__(self,
                 museum_filter: 'MuseumDataFilter',
                 row: int,
                 disabled: bool = False,
                 on_change: typing.Callable = None):
        options = AffiliationSelect.generate_affiliations_select_options(museum_filter=museum_filter)
        super().__init__(options=options,
                         placeholder="Select the affiliation you want to display",
                         custom_id="affiliation_select",
                         row=row,
                         disabled=disabled)
        self.on_change = on_change

    async def callback(self, interaction: discord.Interaction): # TODO j'aime pas du tout ce qui est fait ici
        affiliation_selected: str = interaction.data['values'][0]
        museum_filter = self.view.get_hidden_data()
        if affiliation_selected in ["previous_affiliation", "next_affiliation"]:
            if affiliation_selected == "previous_affiliation":
                museum_filter.affiliation_offset -= 1
            elif affiliation_selected == "next_affiliation":
                museum_filter.affiliation_offset += 1
            self.view.set_hidden_data(museum_filter)
            self.options = AffiliationSelect.generate_affiliations_select_options(museum_filter=museum_filter)
            await self.view.update_menu(interaction=interaction)
        else:
            if affiliation_selected == "all_affiliation":
                museum_filter.set_affiliation(None)
            else:
                museum_filter.set_affiliation(affiliation_selected)
            if self.on_change is not None:
                await self.on_change(self, interaction)

    @staticmethod
    def generate_affiliations_select_options(museum_filter: 'MuseumDataFilter') -> typing.List[discord.SelectOption]:
        affiliations_options: typing.List[discord.SelectOption] = []
        query = Affiliation.select(Affiliation.name)
        affiliations_options.append(discord.SelectOption(label=f"All affiliations",
                                                         value=f"all_affiliation",
                                                         emoji=f"{constants.ASTERISK_EMOJI}"))
        affiliations_options.append(discord.SelectOption(label=f"Previous affiliations",
                                                         value=f"previous_affiliation",
                                                         emoji=f"{constants.LEFT_ARROW_EMOJI}"))
        affiliations_options.append(discord.SelectOption(label=f"Next affiliations",
                                                         value=f"next_affiliation",
                                                         emoji=f"{constants.RIGHT_ARROW_EMOJI}"))
        if museum_filter.affiliation_offset < 0:
            museum_filter.affiliation_offset = 0
        elif museum_filter.affiliation_offset * 22 > len(query):
            museum_filter.affiliation_offset -= 1

        for affiliation in query.paginate(museum_filter.affiliation_offset + 1, 22):
            affiliations_options.append(discord.SelectOption(label=f"{affiliation.name}",
                                                             value=f"{affiliation.name}"))
        return affiliations_options

