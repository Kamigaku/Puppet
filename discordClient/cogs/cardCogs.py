import random
import uuid
from peewee import DoesNotExist
from discord.ext import commands
from discord.ext.commands import Context
from discord import Colour, Embed, Message, User, Emoji

from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener
from discordClient.cogs.abstract import assignableCogs
from discordClient.model.models import Character, CharactersOwnership, Affiliation, CharacterAffiliation, Economy

rarities_label = ["E", "D", "C", "B", "A", "S", "SS"]
rarities_colors_hex = ["9B9B9B", "FFFFFF", "69e15e", "4ccfff", "f0b71c", "f08033", "8f39ce"]
rarities_colors = [Colour(0x9B9B9B), Colour(0xFFFFFF), Colour(0x69e15e), Colour(0x4ccfff), Colour(0xf0b71c),
                   Colour(0xf08033), Colour(0x8f39ce)]
rarities_img_url = "https://www.colorhexa.com/{}.png"


class CardCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "card")
        self.enable()
        self.currently_opening_cards = []

    def enable(self):
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.SELL_EMOJI,
                                                  self.sell_card,
                                                  constants.PUPPET_IDS["CARD_COGS_BUY"]))
        arrow_emojis = [constants.RIGHT_ARROW_EMOJI, constants.LEFT_ARROW_EMOJI]
        self.bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                  arrow_emojis,
                                                  self.display_next_page_drop_list,
                                                  constants.PUPPET_IDS["CARD_COGS_LIST"],
                                                  return_emoji=True))
        self.bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                  arrow_emojis,
                                                  self.display_next_card,
                                                  constants.PUPPET_IDS["CARD_COGS_BUY"],
                                                  return_emoji=True))

    def retrieve_character_id(self, embeds: Embed) -> int:
        return int(self.retrieve_from_embed(embeds, "Character_id: (\d+)"))

    def retrieve_page(self, embeds: Embed) -> int:
        page = self.retrieve_from_embed(embeds, "Page: (\d+)")
        if page:
            return int(page)
        return 0

    def retrieve_offset(self, embeds: Embed) -> int:
        offset = self.retrieve_from_embed(embeds, "Offset: (\d+)")
        if offset:
            return int(offset)
        return 0

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("cards assign")
    async def assign(self, ctx: Context, channel_id: str):
        await self.assign_channel(ctx, channel_id)

    @commands.command()
    async def cards_buy(self, ctx: Context, amount: int = 1):
        self.bot.logger.info(f"Beginning card distribution for user: {ctx.author.id}")
        if ctx.author.id not in self.currently_opening_cards:
            self.currently_opening_cards.append(ctx.author.id)
            user_model, user_created = Economy.get_or_create(discord_user_id=ctx.author.id)
            if user_model.amount >= 20 * amount:
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
                CharactersOwnership.bulk_create(ownerships_models)

                embed_list = generate_embed_list_characters(characters_generated[:10], ctx.author, 0)
                list_message = await ctx.message.reply(content=f"{ctx.author.mention} You have received {5 * amount} "
                                                               f"characters",
                                                       embed=embed_list)
                await list_message.add_reaction(constants.LEFT_ARROW_EMOJI)
                await list_message.add_reaction(constants.RIGHT_ARROW_EMOJI)
                character_embed = generate_embed_character(characters_generated[0], 1)
                character_msg = await list_message.reply(embed=character_embed)
                await character_msg.add_reaction(constants.LEFT_ARROW_EMOJI)
                await character_msg.add_reaction(constants.SELL_EMOJI)
                await character_msg.add_reaction(constants.REPORT_EMOJI)
                await character_msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

                # # Remove the money
                # user_model.amount -= 20
                # user_model.save()

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
        try:
            character_id = self.retrieve_character_id(origin_message.embeds)
            owner = CharactersOwnership.get(discord_user_id=user_that_reacted.id,
                                            character_id=character_id)
            user_model, user_created = Economy.get_or_create(discord_user_id=user_that_reacted.id)
            character_concerned = Character.get_by_id(owner.character_id)
            user_model.amount += character_concerned.rarity
            user_model.save()
            owner.delete_instance()
            await user_that_reacted.send(f"You have sold for {character_concerned.rarity} biteCoin the card"
                                         f" \"{character_concerned.name}\".")
            return
        except DoesNotExist:
            pass

    async def display_next_page_drop_list(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        current_page = self.retrieve_page(origin_message.embeds)
        if emoji.name == constants.LEFT_ARROW_EMOJI:
            current_page -= 1
        elif emoji.name == constants.RIGHT_ARROW_EMOJI:
            current_page += 1
        if current_page < 1:
            return

        query = (Character.select().join(CharactersOwnership)
                          .where(CharactersOwnership.message_id == origin_message.reference.message_id))

        if (current_page - 1) * 10 >= len(query):
            return

        paginated_character = query.paginate(current_page, 10)
        list_embed = generate_embed_list_characters(paginated_character, user_that_reacted, current_page)
        await origin_message.edit(embed=list_embed)

    async def display_next_card(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        owner = origin_message.reference.resolved.mentions[0]
        if owner.id != user_that_reacted.id:
            return
        command_message_id = origin_message.reference.resolved.reference.message_id
        offset_value = self.retrieve_offset(origin_message.embeds)
        if emoji.name == constants.LEFT_ARROW_EMOJI:
            offset_value -= 1
        elif emoji.name == constants.RIGHT_ARROW_EMOJI:
            offset_value += 1
        query = (Character.select().join(CharactersOwnership)
                          .where(CharactersOwnership.message_id == command_message_id))
        character_embed = generate_embed_character(query[offset_value], offset_value)
        await origin_message.edit(embed=character_embed)


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


def generate_embed_character(character: Character, offset = None):
    if len(character.description) > 255:
        character_description = character.description[:255] + "..."
    else:
        character_description = character.description

    embed = Embed(colour=rarities_colors[character.rarity], description=character_description)

    # Thumbnail
    embed.set_thumbnail(url=character.image_link)

    # Author
    embed.set_author(name=character.name, icon_url=rarities_img_url.format(rarities_colors_hex[character.rarity]),
                     url="")

    # Footer
    footer_text = f"Rarity: {rarities_label[character.rarity]}"
    affiliation = ""
    for current_affiliation in (Affiliation.select()
            .join(CharacterAffiliation)
            .join(Character)
            .where(CharacterAffiliation.character_id == character.get_id())
            .group_by(Affiliation)):
        if affiliation:
            affiliation += ", "
        affiliation += current_affiliation.name
    if affiliation:
        footer_text += f" | Affiliation(s): {affiliation}"
    footer_text += f" | Character_id: {character.get_id()} | Puppet_id: {constants.PUPPET_IDS['CARD_COGS_BUY']}"
    if offset is not None:
        footer_text += f" | Offset: {offset}"
    embed.set_footer(text=footer_text, icon_url=rarities_img_url.format(rarities_colors_hex[character.rarity]))
    return embed


def generate_embed_list_characters(characters: list, owner: User, offset: int = 1):
    list_embed = Embed()
    list_embed.set_author(name=f"{owner.name}#{owner.discriminator}", icon_url=owner.avatar_url)
    list_embed.title = "Summary of dropped characters"
    description = "||"
    iteration = 1
    for character in characters:
        description += f"`{(offset - 1)*10+iteration}`. {constants.RARITIES_EMOJI[character.rarity]} " \
                       f"[**{constants.RARITIES_LABELS[character.rarity]}**] {character.name}\n"
        affiliations = (Affiliation.select(Affiliation.name)
                                   .join(CharacterAffiliation)
                                   .where(CharacterAffiliation.character_id == character.id))
        affiliation_text = ""
        for character_affiliation in affiliations:
            affiliation_text += f"{character_affiliation.name}, "
        description += f"{affiliation_text[:-2]}\n"
        iteration += 1
    description += "||"
    list_embed.description = description
    footer = f"Page: {offset} | Puppet_id: {constants.PUPPET_IDS['CARD_COGS_LIST']}"
    list_embed.set_footer(text=footer)
    return list_embed


async def display_character(ctx: Context, character: Character, delete_after: int = 0):
    character_embed = generate_embed_character(character)
    if delete_after == 0:
        msg = await ctx.message.reply(embed=character_embed, mention_author=False)
    else:
        msg = await ctx.message.reply(embed=character_embed, delete_after=delete_after, mention_author=False)
    return msg
