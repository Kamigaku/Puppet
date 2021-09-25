# import datapane as dp
# import pandas as pd
from typing import Any

from discord import User, Emoji
from discord.ext import commands
from discord.ext.commands import Context

from discordClient.cogs import cardCogs
from discordClient.cogs.abstract import AssignableCogs
from discordClient.helper import constants
from discordClient.model import Character, Affiliation, fn, CharacterAffiliation, CharactersOwnership
from discordClient.views import Reaction, PageView123, NumbersListEmbedRender, AllAndNumbersListEmbedRender, \
    PageView, MuseumCharacterListEmbedRender, MuseumCharacterOwnershipListEmbedRender, \
    MuseumAffiliationsNumbersListEmbedRender


# The organisation is the following:
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


class MuseumCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("museum")
    async def museum(self, ctx: Context, owner: User = None):
        character_categories = Character.select(Character.category).group_by(Character.category)
        categories = []
        for character_category in character_categories:
            categories.append(f"{character_category.category}")

        if owner is None:
            museum_filter = MuseumDataFilter(ctx.author)
        else:
            museum_filter = MuseumDataFilter(owner)

        reaction_museum = [Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                    emojis=constants.ASTERISK_EMOJI,
                                    callback=self.display_characters)]

        category_renderer = AllAndNumbersListEmbedRender(menu_title="Select the category you want to display")

        category_menu = PageView123(puppet_bot=self.bot,
                                    elements_to_display=categories,
                                    render=category_renderer,
                                    elements_per_page=10,
                                    reactions=reaction_museum,
                                    callback_number=self.menu_categories_to_choice,
                                    delete_after=600)
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
    async def menu_categories_to_choice(self, menu_update: PageView123, user_that_reacted: User,
                                        emoji: Emoji = None):
        if emoji is None:  # all
            pass
        else:
            index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
            category = menu_update.retrieve_element_by_offset(index)
            if category is None:
                return

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.menu_choices_to_path

            filter_renderer = AllAndNumbersListEmbedRender(menu_title="Select the filter you want to apply")

            menu_update.update_datas(elements_to_display=["Rarities", "Affiliations"],
                                     render=filter_renderer)
            hidden_data = menu_update.retrieve_hidden_data()
            hidden_data.set_category(category=category)
            menu_update.set_hidden_data(hidden_data)
            await menu_update.update_menu()

    # Menu #3 or #4
    async def menu_choices_to_path(self, menu_update: PageView123, user_that_reacted: User,
                                   emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        path = menu_update.retrieve_element_by_offset(index)

        if path is None:
            return

        if index == 0:  # Rarity
            menu_content = []
            for _ in range(0, len(constants.RARITIES_EMOJI)):
                menu_content.append(f"{constants.RARITIES_EMOJI[_]} **{constants.RARITIES_LABELS[_]}**")

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.rarity_selected

            rarities_renderer = NumbersListEmbedRender(menu_title="Select the rarity you want to display")

            menu_update.update_datas(elements_to_display=menu_content,
                                     render=rarities_renderer)

        elif index == 1:  # Affiliations
            menu_content = []
            for letter in constants.LETTER_EMOJIS:
                menu_content.append(f"{letter}")

            reaction = menu_update.retrieve_reaction(emoji.name)
            reaction.callback = self.menu_affiliations_to_path

            rarities_renderer = NumbersListEmbedRender(menu_title="Select the first letter of the affiliation you "
                                                                  "want to display")

            menu_update.update_datas(elements_to_display=menu_content,
                                     render=rarities_renderer)

        await menu_update.update_menu()

    # Menu #5
    async def menu_affiliations_to_path(self, menu_update: PageView123, user_that_reacted: User,
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

        affiliations_renderer = MuseumAffiliationsNumbersListEmbedRender(menu_title="Select the affiliation you want "
                                                                                    "to display")

        menu_update.update_datas(elements_to_display=affiliations_sql,
                                 render=affiliations_renderer)
        await menu_update.update_menu()

    async def affiliation_selected(self, menu_update: PageView123, user_that_reacted: User,
                                   emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        hidden_data = menu_update.retrieve_hidden_data()
        hidden_data.set_affiliation(menu_update.retrieve_element_by_offset(index).name)
        menu_update.set_hidden_data(hidden_data)
        await self.display_characters(menu_update, user_that_reacted, emoji)

    async def rarity_selected(self, menu_update: PageView123, user_that_reacted: User,
                              emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        if index < len(constants.RARITIES_LABELS):
            hidden_data = menu_update.retrieve_hidden_data()
            hidden_data.set_rarity(index)
            menu_update.set_hidden_data(hidden_data)
            await self.display_characters(menu_update, user_that_reacted, emoji)

    async def display_characters(self, menu_update: PageView123, user_that_reacted: User,
                                 emoji: Emoji = None):
        menu_update.remove_reaction(constants.ASTERISK_EMOJI)
        # Characters retrieving
        query = Character.select(Character, fn.Count(Character.id).alias('count'), CharactersOwnership.discord_user_id)
        museum_filter = menu_update.retrieve_hidden_data()
        if museum_filter.category is not None:
            query = query.where(Character.category == museum_filter.category)
        if museum_filter.rarity is not None:
            query = query.where(Character.rarity == museum_filter.rarity)
        if museum_filter.affiliation is not None:
            query = (query.join_from(Character, CharacterAffiliation)
                     .join_from(CharacterAffiliation, Affiliation)
                     .where(Affiliation.name == museum_filter.affiliation))
        total_characters = query.count()

        # Then we filter on only the owned card
        query = (query.join_from(Character, CharactersOwnership, on=(CharactersOwnership.character_id == Character.id))
                      .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                             (CharactersOwnership.is_sold == False))
                      .group_by(Character.id)
                      .order_by(Character.name))

        total_owned = query.count()

        reaction = menu_update.retrieve_reaction(constants.NUMBER_EMOJIS[1])
        reaction.callback = self.display_character

        characters_renderer = MuseumCharacterListEmbedRender(msg_content=f"{museum_filter.owner.name}#"
                                                                         f"{museum_filter.owner.discriminator} "
                                                                         f"currently own "
                                                                         f"{total_owned}/{total_characters} "
                                                                         f"characters.")

        menu_update.update_datas(elements_to_display=query,
                                 render=characters_renderer)
        menu_update.set_hidden_data(hidden_data=query)
        await menu_update.update_menu()

    async def display_character(self, menu_update: PageView123, user_that_reacted: User,
                                emoji: Emoji = None):
        if emoji.name not in constants.NUMBER_EMOJIS:
            return
        offset = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        index = menu_update.retrieve_index(offset)

        character_list = menu_update.retrieve_hidden_data()
        character_concerned = character_list[index]
        ownership_models = (CharactersOwnership.select()
                                               .where((CharactersOwnership.character_id == character_concerned.id) &
                                                      (CharactersOwnership.discord_user_id ==
                                                      character_concerned.charactersownership.discord_user_id) &
                                                      (CharactersOwnership.is_sold == False)))

        reaction_characters = [Reaction(event_type=constants.REACTION_ADD,
                                        emojis=constants.SELL_EMOJI,
                                        callback=cardCogs.sell_card),
                               Reaction(event_type=constants.REACTION_ADD,
                                        emojis=constants.REPORT_EMOJI,
                                        callback=cardCogs.report_card)]

        characters_renderer = MuseumCharacterOwnershipListEmbedRender()

        characters_view = PageView(puppet_bot=self.bot,
                                   elements_to_display=ownership_models,
                                   render=characters_renderer,
                                   bound_to=menu_update.bound_to,
                                   reactions=reaction_characters,
                                   delete_after=60)
        await characters_view.display_menu(menu_update.menu_msg.channel)


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
