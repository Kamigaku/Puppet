import random
import uuid
from itertools import groupby
from discord.ext import commands
from discord.ext.commands import Context
from discord import User, Member
from peewee import fn, JOIN

from discordClient.helper import constants
from discordClient.cogs.abstract import assignableCogs
from discordClient.model import Economy, CharactersOwnership, Character, Affiliation, CharacterAffiliation, Embed
from discordClient.views import PageView, PageModelView, Reaction, Emoji, Fields


class CardCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "card")
        self.currently_opening_cards = []

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command()
    async def cards_buy(self, ctx: Context, amount: int = 1):
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
                                                             message_id=ctx.message.id),
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
                ownerships_models = CharactersOwnership.select().where(CharactersOwnership.message_id == ctx.message.id)

                # Cette section pourrait être transferer dans __str__ de CharactersOwnership
                page_content = []
                for character in characters_generated:
                    character_description = f"{constants.RARITIES_EMOJI[character.rarity]} " \
                                            f"[**{constants.RARITIES_LABELS[character.rarity]}**] {character.name}\n"
                    character_description += character.affiliations
                    page_content.append(character_description)
                # Cette section pourrait être transferer dans __str__ de CharactersOwnership

                page_view = PageView(puppet_bot=self.bot,
                                     msg_content=f"{ctx.author.mention}, you have dropped {5 * amount} characters.",
                                     menu_title="Summary of dropped characters",
                                     elements_to_display=page_content,
                                     elements_per_page=10)
                await page_view.display_menu(ctx)

                reaction_characters = [Reaction(event_type=constants.REACTION_ADD,
                                                emojis=constants.SELL_EMOJI,
                                                callback=sell_card),
                                       Reaction(event_type=constants.REACTION_ADD,
                                                emojis=constants.REPORT_EMOJI,
                                                callback=report_card)]

                characters_view = PageModelView(puppet_bot=self.bot,
                                                elements_to_display=list(ownerships_models),
                                                bound_to=ctx.author,
                                                reactions=reaction_characters)
                await characters_view.display_menu(ctx)
            else:
                await ctx.author.send(f"You don't have enough {constants.COIN_NAME} to buy a booster.")
            self.currently_opening_cards.remove(ctx.author.id)
        else:
            await ctx.author.send("You are already opening a booster. If you think this is an error, contact one of "
                                  "the moderators.")
        self.bot.logger.info(f"Card distribution over for user: {ctx.author.id}")

    @commands.command()
    async def search(self, ctx: Context, name: str):
        if len(name) < 3:
            await ctx.send("The research need to have more than 2 characters.", delete_after=30)
        else:
            mutual_guilds = ctx.author.mutual_guilds
            active_ids = []
            for mutual_guild in mutual_guilds:
                for member in mutual_guild.members:
                    if member.id not in active_ids:
                        active_ids.append(member.id)

            query = (Character.select(Character.id, Character.name, Character.description, Character.image_link,
                                      Character.rarity,
                                      fn.GROUP_CONCAT(CharactersOwnership.discord_user_id, ",").alias("owners"))
                              .join_from(Character, CharactersOwnership,
                                         join_type=JOIN.LEFT_OUTER)
                              .where(Character.name.contains(name))
                              .group_by(Character.id)
                              .order_by(Character.rarity.desc()))

            characters_field = []
            for character in query:
                mutual_owners = []
                if character.owners is not None:
                    splitted_owners = str(character.owners).split(",")
                    for owner in splitted_owners:
                        if int(owner) in active_ids and int(owner) not in mutual_owners:
                            mutual_owners.append(int(owner))
                character_field = Fields(title="Owners of the card",
                                         data=CardOwnerFieldData())
                for mutual_owner in mutual_owners:
                    character_field.data.update_owner(self.bot.get_user(mutual_owner))
                characters_field.append([character_field])

            search_menu = PageModelView(puppet_bot=self.bot,
                                        elements_to_display=list(query),
                                        msg_content=f"Found {query.count()} result(s).",
                                        bound_to=ctx.author,
                                        fields=characters_field,
                                        delete_after=600)
            await search_menu.display_menu(ctx)


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


async def sell_card(menu: PageView, user_that_reacted: User, emoji_used: Emoji):
    ownership_model = menu.retrieve_element(menu.offset)
    if user_that_reacted.id == ownership_model.discord_user_id:
        price_sold = ownership_model.sell()
        if price_sold > 0:
            await user_that_reacted.send(f"You have sold this card for {price_sold} {constants.COIN_NAME}.")
        else:
            await user_that_reacted.send(f"You have already sold this card and cannot sell it again. "
                                         f"If you think this is an error, please communicate to a moderator.")
    else:
        await user_that_reacted.send("You are not the owner of the card, you cannot sell it.")


async def report_card(menu: PageView, user_that_reacted: User, emoji_used: Emoji):
    character_id = menu.retrieve_element(menu.offset).character_id
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
                    value=f"{constants.BOT_PREFIX} report description {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid image__",
                    value=f"{constants.BOT_PREFIX} report image {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid affiliation(s)__",
                    value=f"{constants.BOT_PREFIX} report affiliation {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Invalid name__",
                    value=f"{constants.BOT_PREFIX} report name {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Card incoherency__",
                    value=f"{constants.BOT_PREFIX} report card {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    embed.add_field(name="__Other report__",
                    value=f"{constants.BOT_PREFIX} report other {character_id} **\"[YOUR COMMENT]\"**",
                    inline=False)
    await user_that_reacted.send(embed=embed)


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
