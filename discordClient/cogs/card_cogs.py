import random
import typing
import uuid

from discord.ui import Button
from itertools import groupby

from peewee import fn, JOIN

from discord.ext.commands import slash_command, ApplicationCommandField, InteractionContext
from discordClient.cogs.abstract import AssignableCogs
from discordClient.helper import constants
from discordClient.model import Economy, CharactersOwnership, Character, Affiliation, CharacterAffiliation, \
    CharacterFavorites
from discordClient.views import CharacterListEmbedRender, CharactersEmbedRender, CharactersOwnershipEmbedRender, \
    SellButton, FavoriteButton, LockButton, ReportButton, WishlistRender
from discordClient.views.view import PageView


class CardCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "card")
        self.currently_opening_cards = []

    ################################
    #       COMMAND COGS           #
    ################################

    @slash_command(description="Allow you to buy one or multiple booster.",
                   is_global=True,
                   ephemeral=False)
    @AssignableCogs.restricted
    async def cards_buy(self,
                        ctx: InteractionContext,
                        amount: int = ApplicationCommandField(description="Specify an amount of booster you want to "
                                                                          "buy, the default value being 1.",
                                                              min_value=1,
                                                              default_value=1)):
        self.bot.logger.info(f"Beginning card distribution for user: {ctx.author.id}")
        if ctx.author.id not in self.currently_opening_cards:
            self.currently_opening_cards.append(ctx.author.id)
            economy_model, mode_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            if economy_model.remove_amount(20 * amount):  # Remove the money

                characters_owned_models, characters_models = distribute_cards_to(receiver_id=ctx.author.id,
                                                                                 booster_amount=amount)

                # Recap listing
                page_renderer = CharacterListEmbedRender(msg_content=f"{ctx.author.mention}, you have dropped "
                                                                     f"{5 * amount} characters.",
                                                         menu_title="Summary of dropped characters",
                                                         owner=ctx.author)
                page_view = PageView(puppet_bot=self.bot,
                                     elements_to_display=characters_models,
                                     elements_per_page=10,
                                     render=page_renderer)
                await page_view.display_view(messageable=ctx)

                # First character displaying
                sell_button: Button = SellButton(row=2)
                favorite_button: Button = FavoriteButton(row=2)
                lock_button: Button = LockButton(row=2)
                report_button: Button = ReportButton(row=2)

                common_users = self.bot.get_common_users(ctx.author)
                character_renderer = CharactersOwnershipEmbedRender(common_users=common_users)
                characters_view = PageView(puppet_bot=self.bot,
                                           elements_to_display=characters_owned_models,
                                           elements_per_page=1,
                                           render=character_renderer)
                characters_view.add_items([sell_button, favorite_button, lock_button, report_button])
                await characters_view.display_view(messageable=ctx,
                                                   send_has_reply=False)
            else:
                await ctx.author.send(f"You don't have enough {constants.COIN_NAME} to buy a booster.")
            self.currently_opening_cards.remove(ctx.author.id)
        else:
            await ctx.author.send("You are already opening a booster. If you think this is an error, contact one of "
                                  "the moderators.")
        self.bot.logger.info(f"Card distribution over for user: {ctx.author.id}")

    @slash_command(description="Research a card whose name contains a specified value.",
                   is_global=True,
                   ephemeral=False)
    @AssignableCogs.restricted
    async def search(self, ctx: InteractionContext,
                     name: str = ApplicationCommandField(description="Specify a characters' name value."),
                     affiliation: str = ApplicationCommandField(description="Specify an affiliation's name value."),
                     rarity: int = ApplicationCommandField(description="Specify the rarity's value",
                                                           values={f"{constants.RARITIES_LABELS[index]}": index
                                                                   for index in range(1, 7)}),
                     exact_term: str = ApplicationCommandField(description="If set to 'Exact term', the affiliation "
                                                                           "specified in the request will be the "
                                                                           "exact term searched.",
                                                               values={"Exact term": "1",
                                                                       "Contains": "0"},
                                                               default_value="0")):
        self.bot.logger.debug("Search command started")
        if name is None and affiliation is None and rarity is None:
            await ctx.send(content="The research needs to have at least one filter value.",
                           ephemeral=True)
            return
        if name is not None and len(name) <= 0:
            await ctx.send(content="The 'name' parameter cannot be empty.",
                           ephemeral=True)
            return
        if affiliation is not None and len(affiliation) <= 0:
            await ctx.send(content="The 'affiliation' parameter cannot be empty.",
                           ephemeral=True)
            return
        else:
            query = (Character.select(Character.id, Character.name, Character.description, Character.image_link,
                                      Character.rarity))

            if name is not None:
                if exact_term == "1":
                    query = query.where(Character.name == name)
                else:
                    query = query.where(Character.name.contains(name))
            if rarity is not None:
                query = query.where(Character.rarity == rarity)
            if affiliation is not None:
                if exact_term == "1":
                    query = (query.join_from(Character, CharacterAffiliation)
                             .join_from(CharacterAffiliation, Affiliation)
                             .where(Affiliation.name == affiliation))
                else:
                    query = (query.join_from(Character, CharacterAffiliation)
                             .join_from(CharacterAffiliation, Affiliation)
                             .where(Affiliation.name.contains(affiliation)))
            query = query.order_by(Character.rarity.desc())

            if len(query) > 0:
                # Recap listing
                page_renderer = CharacterListEmbedRender(msg_content=f"Found {query.count()} result(s).",
                                                         menu_title="Summary of found characters",
                                                         owner=ctx.author)
                page_view = PageView(puppet_bot=self.bot,
                                     elements_to_display=query,
                                     elements_per_page=10,
                                     render=page_renderer)
                await page_view.display_view(messageable=ctx)

                # First character displaying
                favorite_button: Button = FavoriteButton(row=2)
                report_button: Button = ReportButton(row=2)
                search_menu_renderer = CharactersEmbedRender(common_users=self.bot.get_common_users(ctx.author))
                search_menu = PageView(puppet_bot=self.bot,
                                       elements_to_display=query,
                                       render=search_menu_renderer,
                                       bound_to=ctx.author,
                                       delete_after=600)
                search_menu.add_items([favorite_button, report_button])
                await search_menu.display_view(messageable=ctx,
                                               send_has_reply=False)
            else:
                await ctx.send(content=f"No results has been found for the query \"{name}\".",
                               ephemeral=True)

    @slash_command(description="Add a complete affiliation as favorite.",
                   is_global=True)
    async def favorite(self,
                       interaction: InteractionContext,
                       affiliation: str = ApplicationCommandField(description="Specify an affiliation's name value.",
                                                                  required=True)):
        await interaction.defer(ephemeral=True)
        if affiliation is None or len(affiliation) <= 0:
            await interaction.send(content="The 'affiliation' parameter cannot be empty.",
                                   ephemeral=True)
            return
        affiliation_model = Affiliation.select(Affiliation.name == affiliation)
        if len(affiliation_model) > 0:
            query = (Character.select(Character.id, Character.name, Character.description, Character.image_link,
                                      Character.rarity, CharacterFavorites.id)
                     .join_from(Character, CharacterAffiliation)
                     .join_from(CharacterAffiliation, Affiliation)
                     .join_from(Character, CharacterFavorites, join_type=JOIN.LEFT_OUTER)
                     .where((Affiliation.name == affiliation) &
                            (CharacterFavorites.character_id == None)))
            if len(query) > 0:
                bulk_favorites = []
                for character in query:
                    bulk_favorites.append(CharacterFavorites(character_id=character.id,
                                                             discord_user_id=interaction.author.id))
                CharacterFavorites.bulk_create(bulk_favorites)
                await interaction.send(content=f"Added {len(query)} new favorites for \"{affiliation}\".",
                                       ephemeral=True)
            else:
                query = (CharacterFavorites.select(CharacterFavorites.id)
                         .join_from(CharacterFavorites, Character, join_type=JOIN.LEFT_OUTER)
                         .join_from(Character, CharacterAffiliation)
                         .join_from(CharacterAffiliation, Affiliation)
                         .where((Affiliation.name == affiliation) &
                                (CharacterFavorites.character_id != None)))
                number_of_deletion = len(query)
                delete_query = CharacterFavorites.delete().where(CharacterFavorites.id.in_(query))
                delete_query.execute()
                await interaction.send(content=f"Removed {number_of_deletion} favorites for \"{affiliation}\".",
                                       ephemeral=True)
        else:
            await interaction.send(content=f"No affiliations has been found for the query \"{affiliation}\".",
                                   ephemeral=True)

    @slash_command(description="Display all the characters that you want and don't own and who are owned by "
                               "someone else.",
                   is_global=True)
    async def wishlist(self,
                       interaction: InteractionContext):
        query = (CharacterFavorites.select(CharacterFavorites.character_id,
                                           Character.description, Character.image_link, Character.rarity,
                                           Character.name, Character.url_link,
                                           fn.GROUP_CONCAT(CharactersOwnership.discord_user_id.distinct()).alias("owners"),
                                           fn.REPLACE(fn.GROUP_CONCAT(Affiliation.name.distinct()), ",", ", ").alias("aff"))
                 .join_from(CharacterFavorites, Character)
                 .join_from(Character, CharactersOwnership)
                 .join_from(Character, CharacterAffiliation)
                 .join_from(CharacterAffiliation, Affiliation)
                 .where((CharacterFavorites.discord_user_id == interaction.author.id) &
                 (CharactersOwnership.discord_user_id != interaction.author.id) &
                 (CharactersOwnership.is_locked == False) &
                 (CharactersOwnership.is_sold == False))
                 .group_by(CharacterFavorites.id)
                 .order_by(Character.rarity.desc(), Character.name, Affiliation.name))
        if len(query) > 0:
            wishlist_renderer = WishlistRender()
            wishlist_view = PageView(puppet_bot=self.bot,
                                     elements_to_display=query,
                                     elements_per_page=1,
                                     render=wishlist_renderer)
            await wishlist_view.display_view(messageable=interaction)
        else:
            await interaction.send(content="Impossible to find something that match your wishlist. Either no one own "
                                           "an unlocked version of your favorites or you have no favorites")

    # @cog_ext.cog_slash(name="test",
    #                    description="Test function for debug purpose")
    # async def search(self, ctx: SlashContext):
    #     starting_time = datetime.datetime.now()
    #     ending_time = starting_time + datetime.timedelta(minutes=90)
    #     r = await ScheduledEvent.create(bot=self.bot,
    #                                     guild_id=877098506211442719,
    #                                     name="code event",
    #                                     privacy_level=ScheduledEventPrivacyLevel.GUILD_ONLY,
    #                                     scheduled_start_time=starting_time,
    #                                     scheduled_end_time=ending_time,
    #                                     entity_type=ScheduledEventEntityType.EXTERNAL,
    #                                     entity_metadata=ScheduledEventEntityMetadata(location="dtc"))
    #     p = await ScheduledEvent.fetch_all(bot=self.bot,
    #                                        guild_id=877098506211442719,
    #                                        with_user_count=True)
    #     s = await ScheduledEvent.fetch(bot=self.bot,
    #                                    guild_id=877098506211442719,
    #                                    guild_scheduled_event_id=r.id)
    #     t = await ScheduledEvent.edit(bot=self.bot,
    #                                   guild_id=877098506211442719,
    #                                   guild_scheduled_event_id=r.id,
    #                                   name="UPDATED DEPUIS LE CODE")
    #     z = await ScheduledEvent.fetch_users(bot=self.bot,
    #                                          guild_id=877098506211442719,
    #                                          guild_scheduled_event_id=r.id,
    #                                          with_member=True)
    #     u = await ScheduledEvent.delete(bot=self.bot,
    #                                     guild_id=877098506211442719,
    #                                     guild_scheduled_event_id=r.id)


def distribute_cards_to(receiver_id: int, booster_amount: int) -> \
        typing.Tuple[typing.List[CharactersOwnership], typing.List[Character]]:
    booster_uuid = uuid.uuid4()
    random.seed(booster_uuid.hex)

    all_rarities = []
    for _ in range(5 * booster_amount):
        all_rarities.append(distribute_random_character([50, 25, 12.5, 9, 3, 0.5]))
    all_rarities.sort()
    all_rarities = [list(it) for k, it in groupby(all_rarities, lambda e: e)]
    characters_and_ownerships = []
    for rarity in all_rarities:
        rarity_character = (Character.select(Character.name, Character.category, Character.rarity,
                                             Character.id,
                                             fn.GROUP_CONCAT(Affiliation.name, ", ").alias("affiliations"))
                            .join_from(Character, CharacterAffiliation)
                            .join_from(CharacterAffiliation, Affiliation)
                            .where(Character.rarity == rarity[0])
                            .group_by(Character.id))
        for _ in range(0, len(rarity)):
            character_generated = rarity_character[random.randrange(0, len(rarity_character) - 1)]
            character_and_ownership = {
                "ownership": CharactersOwnership(discord_user_id=receiver_id,
                                                 character_id=character_generated.get_id()),
                "character": character_generated
            }
            characters_and_ownerships.append(character_and_ownership)

    # Shuffle to prevent straight distribution
    random.shuffle(characters_and_ownerships)

    # Retrieve datas
    ownerships_models = [cao["ownership"] for cao in characters_and_ownerships]
    characters_generated = [cao["character"] for cao in characters_and_ownerships]

    # Db insertion
    CharactersOwnership.bulk_create(ownerships_models)

    # Db retrieving
    ownerships_models_subquery = (CharactersOwnership.select()
                                  .order_by(CharactersOwnership.id.desc())
                                  .limit(5 * booster_amount))
    ownerships_models = (CharactersOwnership.select()
                         .join(ownerships_models_subquery,
                               on=(CharactersOwnership.id == ownerships_models_subquery.c.id))
                         .order_by(CharactersOwnership.id.asc()))
    return ownerships_models, characters_generated


def distribute_random_character(rarities):
    value = random.random() * 100
    current_rarity = 0
    rarity_index = 1
    for rarity in rarities:
        current_rarity += rarity
        if current_rarity > value:
            break
        rarity_index += 1
    return rarity_index


def setup(bot):
    bot.add_cog(CardCogs(bot))
