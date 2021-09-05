# import datapane as dp
# import pandas as pd
from discord import User, Emoji
from discord.ext import commands
from discord.ext.commands import Context
from discordClient.cogs.abstract import assignableCogs
from discordClient.helper import constants
from discordClient.model import Character, Affiliation

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
from discordClient.views import Page123AndAllView


class MuseumCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("museum")
    async def museum(self, ctx: Context):
        menu_title = "Select the category you want to display"
        character_categories = Character.select(Character.category).group_by(Character.category)
        categories = []
        for character_category in character_categories:
            categories.append(f"{character_category.category}")
        category_menu = Page123AndAllView(self.bot, menu_title, categories, 10, self.menu_categories_to_choice, None)
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
    async def menu_categories_to_choice(self, menu_update: Page123AndAllView, user_that_reacted: User,
                                        emoji: Emoji = None):
        if emoji is None:  # all
            pass
        else:
            index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
            category = menu_update.retrieve_element_by_offset(index)
            print(category)
            menu_update.update_datas(menu_title="Select the filter you want to apply",
                                     elements_to_display=["Rarities", "Affiliations"],
                                     callback_letter=self.menu_choices_to_path)
            await menu_update.update_menu()

    # Menu #3 and #4
    async def menu_choices_to_path(self, menu_update: Page123AndAllView, user_that_reacted: User,
                                   emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        path = menu_update.retrieve_element_by_offset(index)
        print(path)

        if index == 0:  # Rarity
            menu_content = []
            for _ in range(0, len(constants.RARITIES_EMOJI)):
                menu_content.append(f"{constants.RARITIES_EMOJI[_]} **{constants.RARITIES_LABELS[_]}**")
            menu_update.update_datas(menu_title="Select the rarity you want to display",
                                     elements_to_display=menu_content,
                                     callback_all=None)
        elif index == 1:  # Affiliations
            menu_content = []
            for letter in constants.LETTER_EMOJIS:
                menu_content.append(f"{letter}")
            menu_update.update_datas(menu_title="Select the first letter of the affiliation you want to display",
                                     elements_to_display=menu_content,
                                     callback_letter=self.menu_affiliations_to_path,
                                     callback_all=None)
        await menu_update.update_menu()

    # Menu #5
    async def menu_affiliations_to_path(self, menu_update: Page123AndAllView, user_that_reacted: User,
                                        emoji: Emoji = None):
        index = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        letter = chr(65 + index)
        print(letter)

        affiliations_sql = (Affiliation.select(Affiliation)
                                       .where(Affiliation.name.startswith(letter))
                                       .order_by(Affiliation.name.asc()))
        affiliations = []
        for affiliation in affiliations_sql:
            affiliations.append(f"{affiliation.name}")

        menu_update.update_datas(menu_title="Select the affiliation you want to display",
                                 elements_to_display=affiliations,
                                 callback_letter=None,
                                 callback_all=None)
        await menu_update.update_menu()
