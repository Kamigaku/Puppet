from typing import Any, List

from discord.ui import Button

from discord import User, Interaction
from peewee import fn, JOIN

from discord.ext.commands import InteractionContext, ApplicationCommandField, slash_command
from discordClient.cogs.abstract import AssignableCogs
from discordClient.model import Character, Affiliation, CharacterAffiliation, CharactersOwnership, CharacterFavorites
from discordClient.views import MuseumCharacterListEmbedRender, CharactersOwnershipEmbedRender, SellButton, \
    LockButton, ReportButton, FavoriteButton, LockFilterButton, UnlockFilterButton, FavoritedFilterButton, \
    NonFavoritedFilterButton, RemoveFilterButton
from discordClient.views.selects import RaritySelect, AffiliationSelect
from discordClient.views.view import PageViewSelectElement, PageView


class MuseumDataFilter:

    def __init__(self,
                 owner: User,
                 category: str | None = None,
                 rarity: List | None = None,
                 affiliation: str | None = None,
                 is_locked: bool | None = None,
                 is_favorited: bool | None = None):
        self.owner = owner
        self.rarity = rarity
        self.affiliation = affiliation
        self.category = category
        self.is_locked: bool | None = is_locked
        self.is_favourited: bool | None = is_favorited
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

    @slash_command(description="Display your collection or to the user specified",
                   is_global=True,
                   ephemeral=False)
    @AssignableCogs.restricted
    async def museum(self,
                     ctx: InteractionContext,
                     user: User = ApplicationCommandField(description="The user you want to check",
                                                          required=False)):
        character_categories = Character.select(Character.category).group_by(Character.category)
        categories = []
        for character_category in character_categories:
            categories.append(f"{character_category.category}")

        if user is None:
            museum_filter = MuseumDataFilter(ctx.author)
        else:
            museum_filter = MuseumDataFilter(user)

        # LIST OF OWNED CHARACTER (list of 10 elements displayed line by line)
        characters_renderer = MuseumCharacterListEmbedRender(msg_content=f"{museum_filter.owner.name}#"
                                                                         f"{museum_filter.owner.discriminator} museum")
        query = (Character.select(Character, fn.Count(Character.id).alias('count'), CharactersOwnership.discord_user_id)
                 .join_from(Character, CharactersOwnership,
                            on=(CharactersOwnership.character_id == Character.id))
                 .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                        (CharactersOwnership.is_sold == False))
                 .group_by(Character.id)
                 .order_by(Character.name))

        category_menu = PageView(puppet_bot=self.bot,
                                 elements_to_display=query,
                                 render=characters_renderer,
                                 delete_after=600,
                                 elements_per_page=10,
                                 callback_next=self.refresh_recap,
                                 callback_prev=self.refresh_recap,
                                 callback_select=self.refresh_recap)
        category_menu.set_hidden_data(museum_filter)
        category_menu.add_items([RaritySelect(row=2,
                                              on_change=self.refresh_museum),  # TODO le select RARITY est mis à jour tout le temps et la selection disparait
                                 AffiliationSelect(museum_filter=museum_filter,
                                                   row=3,
                                                   on_change=self.refresh_museum),
                                 LockFilterButton(row=4,
                                                  callback_method=self.display_locked_character),
                                 UnlockFilterButton(row=4,
                                                    callback_method=self.display_unlocked_character),
                                 FavoritedFilterButton(row=4,
                                                       callback_method=self.display_favorited_character),
                                 NonFavoritedFilterButton(row=4,
                                                          callback_method=self.display_non_favorited_character),
                                 RemoveFilterButton(row=4,
                                                    callback_method=self.remove_filters)])
        await category_menu.display_view(messageable=ctx)

        # OWNERSHIP RECAP LIST - display each ownership one by one
        ownership_query = (CharactersOwnership.select()
                                              .join_from(CharactersOwnership, Character)
                                              .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                                                     (CharactersOwnership.is_sold == False))
                                              .order_by(Character.name))
        sell_button: Button = SellButton(row=2)
        favorite_button: Button = FavoriteButton(row=2)
        lock_button: Button = LockButton(row=2)
        report_button: Button = ReportButton(row=2)

        common_users = self.bot.get_common_users(ctx.author)
        character_renderer = CharactersOwnershipEmbedRender(common_users=common_users)
        self.ownerships_view = PageView(puppet_bot=self.bot,
                                        elements_to_display=ownership_query,
                                        elements_per_page=1,
                                        render=character_renderer)
        self.ownerships_view.add_items([sell_button, favorite_button, lock_button, report_button])
        await self.ownerships_view.display_view(messageable=ctx,
                                                send_has_reply=False)

    ################################
    #       GUI METHODS            #
    ################################

    async def refresh_museum(self,
                             button: AffiliationSelect,
                             interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
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

        if museum_filter.is_locked is not None:
            query = (query.where(CharactersOwnership.is_locked == museum_filter.is_locked))
        if museum_filter.is_favourited is not None:
            if museum_filter.is_favourited:
                query = (query.join_from(Character, CharacterFavorites, join_type=JOIN.LEFT_OUTER)
                              .where(CharacterFavorites.character_id != None))
            else:
                query = (query.join_from(Character, CharacterFavorites, join_type=JOIN.LEFT_OUTER)
                              .where(CharacterFavorites.character_id == None))

        total_owned = query.count()

        characters_renderer = MuseumCharacterListEmbedRender(msg_content=f"{museum_filter.owner.name}#"
                                                                         f"{museum_filter.owner.discriminator} "
                                                                         f"currently own "
                                                                         f"{total_owned}/{total_characters} "
                                                                         f"characters.")

        button.view.update_datas(elements_to_display=query,
                                 render=characters_renderer)
        await button.view.update_view()

        # Refresh the character ownership gui
        ownership_query = (CharactersOwnership.select()
                           .join_from(CharactersOwnership, Character)
                           .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                                  (CharactersOwnership.is_sold == False))
                           .order_by(Character.name))
        if museum_filter.category is not None:
            ownership_query = ownership_query.where(Character.category == museum_filter.category)
        if museum_filter.rarity is not None:
            ownership_query = ownership_query.where(Character.rarity << museum_filter.rarity)
        if museum_filter.affiliation is not None:
            ownership_query = (ownership_query.join_from(Character, CharacterAffiliation)
                                              .join_from(CharacterAffiliation, Affiliation)
                                              .where(Affiliation.name == museum_filter.affiliation))
        if museum_filter.is_locked is not None:
            ownership_query = (ownership_query.where(CharactersOwnership.is_locked == museum_filter.is_locked))
        if museum_filter.is_favourited is not None:
            if museum_filter.is_favourited:
                ownership_query = (ownership_query.join_from(Character, CharacterFavorites, join_type=JOIN.LEFT_OUTER)
                                                  .where(CharacterFavorites.character_id != None))
            else:
                ownership_query = (ownership_query.join_from(Character, CharacterFavorites, join_type=JOIN.LEFT_OUTER)
                                                  .where(CharacterFavorites.character_id == None))
        self.ownerships_view.update_datas(elements_to_display=ownership_query)
        await self.ownerships_view.update_view()

    async def refresh_recap(self, view: PageView, interaction: Interaction):
        first_element_in_list = view.retrieve_element_by_offset()
        starting_point = next(i for i, v in enumerate(self.ownerships_view.elements)
                              if v.character_id.id == first_element_in_list.id)
        await self.ownerships_view.go_to_page(starting_point)

    async def display_locked_character(self,
                                       button: LockFilterButton,
                                       interaction: Interaction):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        museum_filter.is_locked = True
        await self.refresh_museum(button=button,
                                  interaction=interaction)

    async def display_unlocked_character(self,
                                         button: LockFilterButton,
                                         interaction: Interaction):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        museum_filter.is_locked = False
        await self.refresh_museum(button=button,
                                  interaction=interaction)

    async def display_favorited_character(self,
                                       button: LockFilterButton,
                                       interaction: Interaction):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        museum_filter.is_favourited = True
        await self.refresh_museum(button=button,
                                  interaction=interaction)

    async def display_non_favorited_character(self,
                                         button: LockFilterButton,
                                         interaction: Interaction):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        museum_filter.is_favourited = False
        await self.refresh_museum(button=button,
                                  interaction=interaction)

    async def remove_filters(self,
                            button: LockFilterButton,
                            interaction: Interaction):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        museum_filter.is_favourited = None
        museum_filter.is_locked = None
        await self.refresh_museum(button=button,
                                  interaction=interaction)

    async def _locked_unlocked_character(self,
                                         button,
                                         lock_state: bool | None = None):
        museum_filter: MuseumDataFilter = button.view.get_hidden_data()
        query = (
            Character.select(Character, fn.Count(Character.id).alias('count'), CharactersOwnership.discord_user_id)
            .join_from(Character, CharactersOwnership,
                       on=(CharactersOwnership.character_id == Character.id))
            .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                   (CharactersOwnership.is_sold == False) &
                   (CharactersOwnership.is_locked == lock_state))
            .group_by(Character.id)
            .order_by(Character.name))
        button.view.update_datas(elements_to_display=query)
        await button.view.update_view()

        ownership_query = (CharactersOwnership.select()
                           .join_from(CharactersOwnership, Character)
                           .where((CharactersOwnership.discord_user_id == museum_filter.owner.id) &
                                  (CharactersOwnership.is_sold == False) &
                                  (CharactersOwnership.is_locked == lock_state))
                           .order_by(Character.name))
        self.ownerships_view.update_datas(elements_to_display=ownership_query)
        await self.ownerships_view.update_view()


def setup(bot):
    bot.add_cog(MuseumCogs(bot))
