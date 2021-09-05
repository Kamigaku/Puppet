import random
import uuid
from discord.ext import commands
from discord.ext.commands import Context
from discord import Message, User

from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener
from discordClient.cogs.abstract import assignableCogs
from discordClient.model import Economy, CharactersOwnership, Character, Affiliation, CharacterAffiliation
from discordClient.views import PageView, PageModelView


class CardCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "card")
        self.enable()
        self.currently_opening_cards = []

    def enable(self):
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.SELL_EMOJI,
                                                  self.sell_card,
                                                  constants.PUPPET_IDS["CARD_COGS_BUY"],
                                                  remove_reaction=True))

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

                characters_generated = []
                ownerships_models = []
                for _ in range(5 * amount):
                    character_generated = distribute_random_character([50, 25, 12.5, 9, 3, 0.5])
                    ownerships_models.append(CharactersOwnership(discord_user_id=ctx.author.id,
                                                                 character_id=character_generated.get_id(),
                                                                 message_id=ctx.message.id))
                    characters_generated.append(character_generated)

                # Db insertion
                for ownership_model in ownerships_models:
                    ownership_model.save()

                page_title = "Summary of dropped characters"

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

                page_view = PageView(self.bot, page_title, page_content, 10)
                await page_view.display_menu(ctx)

                characters_view = PageModelView(self.bot, ownerships_models, bound_to=ctx.author)
                characters_message = await characters_view.display_menu(ctx)
                await characters_message.add_reaction(constants.SELL_EMOJI)
                await characters_message.add_reaction(constants.REPORT_EMOJI)

                self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                          constants.SELL_EMOJI,
                                                          self.sell_card,
                                                          self.character_message.id,
                                                          bound_to=ctx.author))
            else:
                await ctx.author.send("You don't have enough biteCoin to buy a booster.")
            self.currently_opening_cards.remove(ctx.author.id)
        else:
            await ctx.author.send("You are already opening a booster. If you think this is an error, contact one of "
                                  "the moderators.")
        self.bot.logger.info(f"Card distribution over for user: {ctx.author.id}")

    ################################
    #       CALLBACKS              #
    ################################

    async def sell_card(self, origin_message: Message, user_that_reacted: User):
        ownership_id = self.retrieve_ownership_id(origin_message.embeds)
        if ownership_id:
            ownership_model = CharactersOwnership.get_by_id(ownership_id)
            if user_that_reacted.id == ownership_model.discord_user_id:
                price_sold = ownership_model.sell()
                if price_sold > 0:
                    await user_that_reacted.send(f"You have sold this card for {price_sold} biteCoin.")
                else:
                    await user_that_reacted.send(f"You have already sold this card and cannot sell it again. "
                                                 f"If you think this is an error, please communicate to a moderator.")
            else:
                await user_that_reacted.send("You are not the owner of the card, you cannot sell it.")
        else:
            await user_that_reacted.send("The card you are trying to sell has an invalid format. Please communicate "
                                         "this error to a moderator.")


def distribute_random_character(rarities):
    value = random.random() * 100
    current_rarity = 0
    rarity_index = 1
    for rarity in rarities:
        current_rarity += rarity
        if current_rarity > value:
            break
        rarity_index += 1
    characters = Character.select().where(Character.rarity == rarity_index)
    return characters[random.randrange(0, len(characters) - 1)]
