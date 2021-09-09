import random
import uuid
from itertools import groupby
from discord.ext import commands
from discord.ext.commands import Context
from discord import User

from discordClient.helper import constants
from discordClient.cogs.abstract import assignableCogs
from discordClient.model import Economy, CharactersOwnership, Character, Affiliation, CharacterAffiliation, Embed
from discordClient.views import PageView, PageModelView, PageReaction


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
                    rarity_character = Character.select().where(Character.rarity == rarity[0])
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
                    affiliations = (Affiliation.select(Affiliation.name)
                                    .join(CharacterAffiliation)
                                    .where(CharacterAffiliation.character_id == character.id))
                    character_description += ','.join([a.name for a in affiliations])
                    page_content.append(character_description)
                # Cette section pourrait être transferer dans __str__ de CharactersOwnership

                page_view = PageView(puppet_bot=self.bot,
                                     msg_content=f"{ctx.author.mention}, you have dropped {5 * amount} characters.",
                                     menu_title="Summary of dropped characters",
                                     elements_to_display=page_content,
                                     elements_per_page=10)
                await page_view.display_menu(ctx)

                reaction_characters = [PageReaction(event_type=constants.REACTION_ADD,
                                                    emojis=constants.SELL_EMOJI,
                                                    callback=self.sell_card),
                                       PageReaction(event_type=constants.REACTION_ADD,
                                                    emojis=constants.REPORT_EMOJI,
                                                    callback=self.report_card)]

                characters_view = PageModelView(puppet_bot=self.bot,
                                                elements_to_display=ownerships_models,
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

    ################################
    #       CALLBACKS              #
    ################################

    async def sell_card(self, menu: PageView, user_that_reacted: User, emoji_used):
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

    async def report_card(self, menu: PageView, user_that_reacted: User):
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
