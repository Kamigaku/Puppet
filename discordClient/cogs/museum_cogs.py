# import datapane as dp
# import pandas as pd
from typing import Any, List

from discord import User
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_select_option, create_select
from peewee import fn

from discordClient.cogs.abstract import AssignableCogs
from discordClient.helper import constants
from discordClient.model import Character, Affiliation, CharacterAffiliation, CharactersOwnership
from discordClient.views import Reaction, PageView, MuseumCharacterListEmbedRender, \
    ViewReactionsLine, ViewWithReactions, PageViewSelectElement, CharactersOwnershipEmbedRender


class MuseumDataFilter:

    def __init__(self, owner: User, category: Any = None, rarity: List = None, affiliation: Any = None):
        self.owner = owner
        self.rarity = rarity
        self.affiliation = affiliation
        self.category = category
        self.affiliation_offset = 0

    def __str__(self):
        return f"MuseumFilter:\n\t- {self.owner}\n\t- {self.category}\n\t- {self.rarity}\n\t- {self.affiliation}"

    def set_rarity(self, rarity):
        self.rarity = rarity

    def set_affiliation(self, affiliation: Any):
        self.affiliation = affiliation

    def set_owner(self, owner: User):
        self.owner = owner

    def set_category(self, category: Any):
        self.category = category


class MuseumCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")

    ################################
    #       COMMAND COGS           #
    ################################

    @cog_ext.cog_slash(name="museum",
                       description="Display your complete collection",
                       options=[
                           create_option(name="user", description="The user to check",
                                         option_type=SlashCommandOptionType.USER, required=False)
                       ])
    @AssignableCogs.restricted
    async def museum(self, ctx: SlashContext, user: User = None):
        character_categories = Character.select(Character.category).group_by(Character.category)
        categories = []
        for character_category in character_categories:
            categories.append(f"{character_category.category}")

        if user is None:
            museum_filter = MuseumDataFilter(ctx.author)
        else:
            museum_filter = MuseumDataFilter(user)

        # Rarities selection
        rarity_select_line = ViewReactionsLine()
        rarity_select_line.add_reaction(Reaction(button=constants.RARITY_SELECT, callback=self.rarity_selected))

        # Affiliation selection
        affiliation_select = self.generate_affiliations_select(museum_filter)
        affiliation_select_line = ViewReactionsLine()
        affiliation_select_line.add_reaction(Reaction(button=affiliation_select, callback=self.affiliation_selected))

        # Gui creation
        characters_renderer = MuseumCharacterListEmbedRender(msg_content=f"{museum_filter.owner.name}#"
                                                                         f"{museum_filter.owner.discriminator} museum")

        # Query
        query = (Character.select(Character, fn.Count(Character.id).alias('count'), CharactersOwnership.discord_user_id)
                 .join_from(Character, CharactersOwnership,
                            on=(CharactersOwnership.character_id == Character.id))
                 .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                        (CharactersOwnership.is_sold == False))
                 .group_by(Character.id)
                 .order_by(Character.name))

        category_menu = PageViewSelectElement(puppet_bot=self.bot,
                                              elements_to_display=query,
                                              render=characters_renderer,
                                              lines=[rarity_select_line, affiliation_select_line],
                                              callback_element_selection=self.display_character,
                                              delete_after=600,
                                              elements_per_page=10)
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
    #       CALLBACKS GUI          #
    ################################

    async def affiliation_selected(self, **t):
        context = t["context"]
        menu = t["menu"]
        affiliation_selected = context.selected_options[0]
        museum_filter = menu.get_hidden_data()
        if affiliation_selected in ["previous_affiliation", "next_affiliation"]:
            if affiliation_selected == "previous_affiliation":
                museum_filter.affiliation_offset -= 1
            elif affiliation_selected == "next_affiliation":
                museum_filter.affiliation_offset += 1
            menu.set_hidden_data(museum_filter)
            reaction_affiliation = menu.retrieve_button("affiliation_select")
            reaction_affiliation.button = self.generate_affiliations_select(museum_filter)
            await menu.update_menu(context)
        else:
            if affiliation_selected == "all_affiliation":
                museum_filter.set_affiliation(None)
            else:
                museum_filter.set_affiliation(affiliation_selected)
            await self.refresh_museum(context, menu, museum_filter)

    async def rarity_selected(self, **t):
        context = t["context"]
        menu = t["menu"]
        museum_filter = menu.get_hidden_data()
        museum_filter.set_rarity(context.selected_options)
        await self.refresh_museum(context, menu, museum_filter)

    ################################
    #       GUI METHODS            #
    ################################

    @staticmethod
    async def refresh_museum(context, menu: ViewWithReactions, museum_filter: MuseumDataFilter):
        query = Character.select(Character, fn.Count(Character.id).alias('count'), CharactersOwnership.discord_user_id)
        if museum_filter.category is not None:
            query = query.where(Character.category == museum_filter.category)
        if museum_filter.rarity is not None:
            query = query.where(Character.rarity << museum_filter.rarity)
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

        characters_renderer = MuseumCharacterListEmbedRender(msg_content=f"{museum_filter.owner.name}#"
                                                                         f"{museum_filter.owner.discriminator} "
                                                                         f"currently own "
                                                                         f"{total_owned}/{total_characters} "
                                                                         f"characters.")

        menu.update_datas(elements_to_display=query,
                          render=characters_renderer)
        await menu.update_menu(context)

    @staticmethod
    def generate_affiliations_select(museum_filter: MuseumDataFilter):
        # Affiliation selection
        affiliations_options = []
        query = Affiliation.select(Affiliation.name)
        affiliations_options.append(create_select_option(f"All affiliations",
                                                         value=f"all_affiliation",
                                                         emoji=f"{constants.ASTERISK_EMOJI}"))
        affiliations_options.append(create_select_option(f"Previous affiliations",
                                                         value=f"previous_affiliation",
                                                         emoji=f"{constants.LEFT_ARROW_EMOJI}"))
        affiliations_options.append(create_select_option(f"Next affiliations",
                                                         value=f"next_affiliation",
                                                         emoji=f"{constants.RIGHT_ARROW_EMOJI}"))
        if museum_filter.affiliation_offset < 0:
            museum_filter.affiliation_offset = 0
        elif museum_filter.affiliation_offset * 22 > len(query):
            museum_filter.affiliation_offset -= 1

        for affiliation in query.paginate(museum_filter.affiliation_offset + 1, 22):
            affiliations_options.append(create_select_option(f"{affiliation.name}",
                                                             value=f"{affiliation.name}"))
        affiliation_select = create_select(options=affiliations_options,
                                           placeholder="Select the affiliation you want to display",
                                           custom_id="affiliation_select")
        return affiliation_select

    async def display_character(self, context: ComponentContext,
                                menu: PageViewSelectElement, selected_index: int, selected_element: Character):
        await context.defer(ignore=True)
        ownership_models = (CharactersOwnership.select()
                            .where((CharactersOwnership.character_id == selected_element.id) &
                                   (CharactersOwnership.discord_user_id ==
                                    selected_element.charactersownership.discord_user_id) &
                                   (CharactersOwnership.is_sold == False)))

        common_users = self.bot.get_common_users(menu.get_hidden_data().owner)
        characters_renderer = CharactersOwnershipEmbedRender(common_users=common_users)

        actions_line = ViewReactionsLine()
        if menu.get_hidden_data().owner.id == context.author_id:
            actions_line.add_reaction(Reaction(button=constants.SELL_BUTTON, callback=cardCogs.sell_card))
        actions_line.add_reaction(Reaction(button=constants.FAVORITE_BUTTON, callback=cardCogs.favorite_card))
        if menu.get_hidden_data().owner.id == context.author_id:
            actions_line.add_reaction(Reaction(button=constants.LOCK_BUTTON, callback=cardCogs.lock_card))
        actions_line.add_reaction(Reaction(button=constants.REPORT_BUTTON, callback=cardCogs.report_card))

        characters_view = PageView(puppet_bot=self.bot,
                                   elements_to_display=ownership_models,
                                   render=characters_renderer,
                                   bound_to=menu.bound_to,
                                   lines=[actions_line],
                                   delete_after=60)
        await characters_view.display_menu(menu.menu_msg.channel)
