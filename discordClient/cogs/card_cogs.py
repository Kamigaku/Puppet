import random
import uuid
from itertools import groupby

from discord import Member, Embed
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, create_choice
from peewee import fn

from discordClient.cogs.abstract import AssignableCogs
from discordClient.helper import constants
from discordClient.model import Economy, CharactersOwnership, Character, Affiliation, CharacterAffiliation, \
    CharacterFavorites
from discordClient.views import PageView, Reaction, CharacterListEmbedRender, ViewReactionsLine, \
    CharactersEmbedRender, CharactersOwnershipEmbedRender


class CardCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "card")
        self.currently_opening_cards = []

    ################################
    #       COMMAND COGS           #
    ################################

    @cog_ext.cog_slash(name="cards_buy",
                       description="Allow you to buy one or multiple booster.",
                       options=[
                           create_option(
                               name="amount",
                               description="Specify an amount of booster you want to buy, the default value being 1.",
                               option_type=4,
                               required=False
                           )
                       ])
    @AssignableCogs.restricted
    async def cards_buy(self, ctx: SlashContext, amount: int = 1):
        self.bot.logger.info(f"Beginning card distribution for user: {ctx.author.id}")
        if ctx.author.id not in self.currently_opening_cards:
            self.currently_opening_cards.append(ctx.author.id)
            economy_model, mode_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            if economy_model.remove_amount(20 * amount):  # Remove the money
                booster_uuid = uuid.uuid4()
                random.seed(booster_uuid.hex)

                all_rarities = []
                for _ in range(5 * amount):
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
                            "ownership": CharactersOwnership(discord_user_id=ctx.author.id,
                                                             character_id=character_generated.get_id(),
                                                             message_id=ctx.interaction_id),
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
                characters_owned_models = (CharactersOwnership.select()
                                           .where(CharactersOwnership.message_id == ctx.interaction_id))

                # Recap listing
                page_renderer = CharacterListEmbedRender(msg_content=f"{ctx.author.mention}, you have dropped "
                                                                     f"{5 * amount} characters.",
                                                         menu_title="Summary of dropped characters")
                page_view = PageView(puppet_bot=self.bot,
                                     elements_to_display=characters_generated,
                                     elements_per_page=10,
                                     render=page_renderer)
                await page_view.display_menu(ctx)

                # First character displaying
                actions_line = ViewReactionsLine()
                actions_line.add_reaction(Reaction(button=constants.SELL_BUTTON, callback=sell_card))
                actions_line.add_reaction(Reaction(button=constants.FAVORITE_BUTTON, callback=favorite_card))
                actions_line.add_reaction(Reaction(button=constants.LOCK_BUTTON, callback=lock_card))
                actions_line.add_reaction(Reaction(button=constants.REPORT_BUTTON, callback=report_card))

                common_users = self.bot.get_common_users(ctx.author)
                character_renderer = CharactersOwnershipEmbedRender(common_users=common_users)
                characters_view = PageView(puppet_bot=self.bot,
                                           elements_to_display=characters_owned_models,
                                           lines=[actions_line],
                                           elements_per_page=1,
                                           render=character_renderer)
                await characters_view.display_menu(ctx)
            else:
                await ctx.author.send(f"You don't have enough {constants.COIN_NAME} to buy a booster.")
            self.currently_opening_cards.remove(ctx.author.id)
        else:
            await ctx.author.send("You are already opening a booster. If you think this is an error, contact one of "
                                  "the moderators.")
        self.bot.logger.info(f"Card distribution over for user: {ctx.author.id}")

    @cog_ext.cog_slash(name="search",
                       description="Research a card whose name contains a specified value.",
                       options=[
                           create_option(
                               name="name",
                               description="Specify a characters' name value.",
                               option_type=SlashCommandOptionType.STRING,
                               required=False
                           ),
                           create_option(
                               name="affiliation",
                               description="Specify an affiliation's name value.",
                               option_type=SlashCommandOptionType.STRING,
                               required=False
                           ),
                           create_option(
                               name="rarity",
                               description="Specify the rarity's value",
                               option_type=SlashCommandOptionType.INTEGER,
                               choices=[create_choice(name=f"{constants.RARITIES_LABELS[index]}",
                                                      value=index)
                                        for index in range(1, 7)],
                               required=False
                           )
                       ])
    @AssignableCogs.restricted
    async def search(self, ctx: SlashContext, name: str = None, affiliation: str = None, rarity: int = None):
        self.bot.logger.debug("Search command started")
        if name is None and affiliation is None and rarity is None:
            await ctx.send(content="The research needs to have at least one filter value.",
                           hidden=True)
            return
        if name is not None and len(name) < 3:
            await ctx.send(content="The 'name' parameter needs to have more than 2 characters.",
                           hidden=True)
            return
        if affiliation is not None and len(affiliation) < 3:
            await ctx.send(content="The 'affiliation' parameter needs to have more than 2 characters.",
                           hidden=True)
            return
        else:
            query = (Character.select(Character.id, Character.name, Character.description, Character.image_link,
                                      Character.rarity))

            if name is not None:
                query = query.where(Character.name.contains(name))
            if rarity is not None:
                query = query.where(Character.rarity == rarity)
            if affiliation is not None:
                query = (query.join_from(Character, CharacterAffiliation)
                         .join_from(CharacterAffiliation, Affiliation)
                         .where(Affiliation.name.contains(affiliation)))
            query = query.order_by(Character.rarity.desc())

            if len(query) > 0:
                # First character displaying
                actions_line = ViewReactionsLine()
                actions_line.add_reaction(Reaction(button=constants.FAVORITE_BUTTON, callback=favorite_card))
                actions_line.add_reaction(Reaction(button=constants.REPORT_BUTTON, callback=report_card))
                search_menu_renderer = CharactersEmbedRender(msg_content=f"Found {query.count()} result(s).",
                                                             common_users=self.bot.get_common_users(ctx.author))
                search_menu = PageView(puppet_bot=self.bot,
                                       elements_to_display=query,
                                       render=search_menu_renderer,
                                       bound_to=ctx.author,
                                       lines=[actions_line],
                                       delete_after=600)
                await search_menu.display_menu(ctx)
            else:
                await ctx.send(f"No results has been found for the query \"{name}\".")


class CardOwnerFieldData:

    def __init__(self):
        self.owners = []

    def __str__(self):
        if len(self.owners) == 0:
            return "Nobody"
        else:
            character_list = ""
            for owner in self.owners:
                character_list += f"{owner.name}#{owner.discriminator}\n"
            return character_list

    def update_owner(self, owner: Member):
        if owner in self.owners:
            self.owners.remove(owner)
        else:
            self.owners.append(owner)

    def has_data(self):
        return len(self.owners) > 0


async def favorite_card(**t):
    menu = t["menu"]
    user_that_interact = t["user_that_interact"]
    context = t["context"]
    character_model = menu.retrieve_element(menu.page)
    if type(character_model) is CharactersOwnership:
        character_model = character_model.character_id
    model, model_created = CharacterFavorites.get_or_create(character_id=character_model.id,
                                                            discord_user_id=user_that_interact.id)
    if not model_created:
        model.delete_instance()
    if model_created:
        await context.send(f"You added to your favorites the card {character_model}.", hidden=True)
    else:
        await context.send(f"You removed from your favorites the card {character_model}.", hidden=True)


async def lock_card(**t):
    menu = t["menu"]
    user_that_interact = t["user_that_interact"]
    context = t["context"]
    ownership_model = menu.retrieve_element(menu.page)
    if user_that_interact.id == ownership_model.discord_user_id:
        new_state = ownership_model.lock()
        if new_state:
            await context.send(f"You have locked the card {ownership_model}.", hidden=True)
        else:
            await context.send(f"You have unlocked the card {ownership_model}.", hidden=True)
    else:
        await context.send("You are not the owner of the card, you cannot lock it.", hidden=True)


async def sell_card(**t):
    menu = t["menu"]
    user_that_interact = t["user_that_interact"]
    context = t["context"]
    ownership_model = menu.retrieve_element(menu.page)
    if user_that_interact.id == ownership_model.discord_user_id:
        price_sold = ownership_model.sell()
        if price_sold > 0:
            await user_that_interact.send(f"You have sold this card for {price_sold} {constants.COIN_NAME}.")
            await context.defer(ignore=True)
        else:
            await context.send(f"You have already sold this card and cannot sell it again. "
                               f"If you think this is an error, please communicate to a moderator.", hidden=True)
    else:
        await context.send("You are not the owner of the card, you cannot sell it.", hidden=True)


async def report_card(**t):
    menu = t["menu"]
    user_that_interact = t["user_that_interact"]
    context = t["context"]
    character_id = menu.retrieve_element(menu.page).character_id
    character = Character.get_by_id(character_id)
    embed = Embed()
    embed.title = f"{constants.REPORT_EMOJI} Report a card"
    embed.colour = 0xFF0000
    embed.description = f"Hello, you are on your way to report the card **{character.name}**.\n\n"
    embed.description += "Reporting a card means that the current card has something that you judge " \
                         "incoherent, invalid or maybe because the card should not exist.\n\n **__Please " \
                         "note that your report will be sent to a moderator that will review them in " \
                         "order to judge if they are valid or not. Do not add any personal datas or " \
                         "anything that could lead to a ban of the Puppet project.__**\n\n To be more " \
                         "precise on the category of your report, you will find below a list of commands " \
                         "that you can send to describe the type of report you want to do : "
    embed.set_thumbnail(url=character.image_link)
    embed.add_field(name="__Description incoherency__",
                    value=f"/report description {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid image__",
                    value=f"/report image {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid affiliation(s)__",
                    value=f"/report affiliation {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid name__",
                    value=f"/report name {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Card incoherency__",
                    value=f"/report card {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Other report__",
                    value=f"/report other {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    await user_that_interact.send(embed=embed)
    await context.defer(ignore=True)


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