import random
import uuid
from peewee import DoesNotExist
from discord.ext import commands
from discord.ext.commands import Context
from discord import Colour, Embed, RawReactionActionEvent
from discordClient.helper import constants
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

    def retrieve_character_id(self, embeds: Embed) -> int:
        return int(self.retrieve_from_embed(embeds, "Character_id: (\d+)"))

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("cards assign")
    async def assign(self, ctx: Context, channel_id: str):
        await self.assign_channel(ctx, channel_id)

    @commands.command("cards_buy")
    async def buy_booster(self, ctx: Context):
        user_model, user_created = Economy.get_or_create(discord_user_id=ctx.author.id)
        if user_model.amount >= 20:
            booster_uuid = uuid.uuid4()
            random.seed(booster_uuid.hex)
            await ctx.message.reply(content=f"Booster generated for user {ctx.message.author.mention}",
                                    mention_author=False)
            msg_cards = []
            for _ in range(5):
                character_generated = distribute_random_character([50, 25, 12.5, 9, 3, 0.5])
                msg = await display_character(ctx, character_generated)
                ownership_model, has_created_model = CharactersOwnership.get_or_create(
                    discord_user_id=ctx.author.id, character_id=character_generated.get_id(), message_id=msg.id)
                ownership_model.save()
                msg_cards.append(msg)

            for msg in msg_cards:
                await msg.add_reaction(constants.SELL_EMOJI)
                #await msg.add_reaction(constants.LIBRARY_EMOJI)
                await msg.add_reaction(constants.REPORT_EMOJI)

            user_model.amount -= 20
            user_model.save()
        else:
            await ctx.author.send("You don't have enough biteCoin to buy a booster.")

    ################################
    #       LISTENER COGS          #
    ################################

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        ####
        # Init actions
        if self.bot.user.id == payload.user_id:  # We avoid to react to the current bot reactions
            return

        # We avoid situation that doesn't matter
        user_that_reacted = await self.retrieve_member(payload.user_id)
        if user_that_reacted.bot is True or payload.event_type != "REACTION_ADD":
            return

        # Variables that are needed to determine path
        origin_message = await self.retrieve_message(payload.channel_id, payload.message_id)
        replied_message = await self.retrieve_origin_reply_message(origin_message)

        # We exit if the user that react is not the one that sent the command
        if replied_message.author.id != payload.user_id:
            return

        puppet_id = self.retrieve_puppet_id(origin_message.embeds)
        # End Init Actions
        ####

        # We filter only on what we seek
        if puppet_id == constants.PUPPET_IDS["CARD_COGS_BUY"]:
            if str(payload.emoji) == constants.SELL_EMOJI:  # We sell the card
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
                    channel = self.bot.get_channel(payload.channel_id)
                    msg = await channel.fetch_message(payload.message_id)
                    await msg.remove_reaction(payload.emoji, user_that_reacted)
            elif str(payload.emoji) == constants.LIBRARY_EMOJI:  # We display the affiliations associated to the card
                print("lib")


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


def generate_embed_character(character: Character):
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
    embed.set_footer(text=footer_text, icon_url=rarities_img_url.format(rarities_colors_hex[character.rarity]))
    return embed


async def display_character(ctx: Context, character: Character, delete_after: int = 0):
    character_embed = generate_embed_character(character)
    if delete_after == 0:
        msg = await ctx.message.reply(embed=character_embed, mention_author=False)
    else:
        msg = await ctx.message.reply(embed=character_embed, delete_after=delete_after, mention_author=False)
    return msg
