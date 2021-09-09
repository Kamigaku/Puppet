# import datapane as dp
# import pandas as pd
from typing import Any

from discord import User, Emoji
from discord.ext import commands
from discord.ext.commands import Context
from discordClient.cogs.abstract import assignableCogs
from discordClient.helper import constants
from discordClient.model import Character, Affiliation, fn, CharacterAffiliation, CharactersOwnership
from discordClient.views import PageViewWithReactions, PageReaction


# The organisation is like that
#
#    #####################    #####################      #####################
#    # MENU - Categories #    # MENU - Choice     #      # MENU - Rarity     #
#    #    A - Disney     #    #    A - Rarity     #  A   #    A - Common     #
#    #    ...            # => #    B - Affiliation# ===> #    B - Rary       # ==============================>|
#    #    * - All      1 #    #    * - All      2 #      #    ...            #                                |
#    #####################    #####################      #    * - All      3 #                                |
#                                      |                 #####################                                |
#                                      |                                                                      |
#                                      |                 #####################         #####################  |
#                                      |                 # MENU - Letter     #   si    # MENU - Feature    #  |
#                                      |         B       #    A              # B avant #    A              # >|
#                                      |==============>  #    ...            #   ===>  #    ...            #  |
#                                      |                 #    J            4 #         #    J            5 #  |
#                                      |                 #####################         #####################  |
#                                      |                                                                      |
#                                      |                                                            v=========|
#                                      |                                                 #####################
#                                      | si *                                            # Affichage perso   #
#                                      |================================================>#                   #
#                                                                                        #                   # ==| Loop
#                                                                                        #                 6 # <=|
#                                                                                        #####################
#


class MuseumCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("museum")
    async def museum(self, ctx: Context, owner: User = None):
        menu_title = "Select the category you want to display"
        character_categories = Character.select(Character.category).group_by(Character.category)
        categories = []
        for character_category in character_categories:
            categories.append(f"{character_category.category}")

        if owner is None:
            museum_filter = MuseumDataFilter(ctx.author)
        else:
            museum_filter = MuseumDataFilter(owner)

        reaction_museum = [PageReaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                        emojis=constants.NUMBER_EMOJIS[1:],
                                        callback=self.menu_categories_to_choice),
                           PageReaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                        emojis=constants.ASTERISK_EMOJI,
                                        callback=self.display_characters)]

        category_menu = PageViewWithReactions(puppet_bot=self.bot,
                                              menu_title=menu_title,
                                              elements_to_display=categories,
                                              elements_per_page=10,
                                              author=museum_filter.owner,
                                              reactions=reaction_museum)
        category_menu.set_hidden_data(museum_filter)
        await category_menu.display_menu(ctx)

    # @commands.command("report")
    # async def report(self, ctx: Context):
    #     query = (Character.select(Character.name, Character.description, Character.category, Character.rarity)
    #                       .join(CharactersOwnership))
    #     df = pd.DataFrame(list(query.dicts()))
    #     r = dp.Report(
    #         dp.Markdown('My simple report'),  # add description to the report
    #         dp.DataTable(df),  # create a table
    #     )
    #
    #     # Publish your report. Make sure to have visibility='PUBLIC' if you want to share your report
    #     r.save(path='report.html')

    ################################
    #       CALLBACKS              #
    ################################

    # Menu #2
    async def menu_categories_to_choice(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                                        emoji: Emoji = None):
        if emoji is None:  # all
            pass
        else:
            index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
            category = menu_update.retrieve_element_by_offset(index)

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.menu_choices_to_path

            menu_update.update_datas(menu_title="Select the filter you want to apply",
                                     elements_to_display=["Rarities", "Affiliations"])
            hidden_data = menu_update.retrieve_hidden_data()
            hidden_data.set_category(category=category)
            menu_update.set_hidden_data(hidden_data)
            await menu_update.update_menu()

    # Menu #3 or #4
    async def menu_choices_to_path(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                                   emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        path = menu_update.retrieve_element_by_offset(index)

        if index == 0:  # Rarity
            menu_content = []
            for _ in range(0, len(constants.RARITIES_EMOJI)):
                menu_content.append(f"{constants.RARITIES_EMOJI[_]} **{constants.RARITIES_LABELS[_]}**")

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.rarity_selected

            menu_update.update_datas(menu_title="Select the rarity you want to display",
                                     reset_counter_on_each_page=True,
                                     elements_to_display=menu_content)

        elif index == 1:  # Affiliations
            menu_content = []
            for letter in constants.LETTER_EMOJIS:
                menu_content.append(f"{letter}")

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.menu_affiliations_to_path

            menu_update.update_datas(menu_title="Select the first letter of the affiliation you want to display",
                                     reset_counter_on_each_page=True,
                                     elements_to_display=menu_content)

        await menu_update.update_menu()

    # Menu #5
    async def menu_affiliations_to_path(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                                        emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        letter_emoji = menu_update.retrieve_element_by_offset(index)
        letter_index = constants.LETTER_EMOJIS.index(letter_emoji)
        letter = chr(65 + letter_index)

        affiliations_sql = (Affiliation.select(Affiliation)
                                       .where(Affiliation.name.startswith(letter))
                                       .order_by(Affiliation.name.asc()))

        reaction = menu_update.retrieve_reaction(emoji.name)
        reaction.callback = self.affiliation_selected

        menu_update.update_datas(menu_title="Select the affiliation you want to display",
                                 elements_to_display=affiliations_sql)
        await menu_update.update_menu()

    async def affiliation_selected(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                                   emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        hidden_data = menu_update.retrieve_hidden_data()
        hidden_data.set_affiliation(menu_update.retrieve_element_by_offset(index).name)
        menu_update.set_hidden_data(hidden_data)
        await self.display_characters(menu_update, emoji)

    async def rarity_selected(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                              emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        if index < len(constants.RARITIES_LABELS):
            hidden_data = menu_update.retrieve_hidden_data()
            hidden_data.set_rarity(index)
            menu_update.set_hidden_data(hidden_data)
            await self.display_characters(menu_update, emoji)

    async def display_characters(self, menu_update: PageViewWithReactions, emoji: Emoji = None):
        # Characters retrieving
        query = Character.select(Character, fn.Count(Character.id).alias('count'))
        museum_filter = menu_update.retrieve_hidden_data()
        if museum_filter.category is not None:
            query = query.where(Character.category == museum_filter.category)
        if museum_filter.rarity is not None:
            query = query.where(Character.rarity == museum_filter.rarity)
        if museum_filter.affiliation is not None:
            query = (query.join(CharacterAffiliation)
                     .join(Affiliation)
                     .where(Affiliation.name == museum_filter.affiliation))
        total_characters = query.count()

        # Then we filter on only the owned card
        query = (query.join(CharactersOwnership, on=(CharactersOwnership.character_id == Character.id))
                 .where(CharactersOwnership.discord_user_id == museum_filter.owner.id)
                 .group_by(Character.id)
                 .order_by(Character.name))

        total_owned = query.count()

        museum_characters = []
        for character in query:
            affiliations = (Affiliation.select(Affiliation.name)
                            .join(CharacterAffiliation)
                            .where(CharacterAffiliation.character_id == character.id))
            affiliation_text = ", ".join([a.name for a in affiliations])
            character_field = f"{constants.RARITIES_EMOJI[character.rarity]} " \
                              f"**[{constants.RARITIES_LABELS[character.rarity]}] {character.name}**"
            if character.count > 1:
                character_field += f" (x{character.count})"
            character_field += f"\n{affiliation_text}\n"
            museum_characters.append(character_field)

        reaction = menu_update.retrieve_reaction(emoji.name)
        reaction.callback = self.display_character

        menu_update.update_datas(msg_content=f"{museum_filter.owner.name}#{museum_filter.owner.discriminator} "
                                             f"currently own {total_owned}/{total_characters} characters.",
                                 menu_title="",
                                 elements_to_display=museum_characters)
        await menu_update.update_menu()

    async def display_character(self, menu_update: PageViewWithReactions, user_that_reacted: User,
                                emoji: Emoji = None):
        pass


class MuseumDataFilter:

    def __init__(self, owner: User, category: Any = None, rarity: Any = None, affiliation: Any = None):
        self.owner = owner
        self.rarity = rarity
        self.affiliation = affiliation
        self.category = category

    def __str__(self):
        return f"MuseumFilter:\n\t- {self.owner}\n\t- {self.category}\n\t- {self.rarity}\n\t- {self.affiliation}"

    def set_rarity(self, rarity: Any):
        self.rarity = rarity

    def set_affiliation(self, affiliation: Any):
        self.affiliation = affiliation

    def set_owner(self, owner: User):
        self.owner = owner

    def set_category(self, category: Any):
        self.category = category
