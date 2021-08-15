import math
import datapane as dp
import pandas as pd
from peewee import fn
from discord import Embed, RawReactionActionEvent, Message
from discord.ext import commands
from discord.ext.commands import Context
from discordClient.cogs.abstract import assignableCogs
from discordClient.helper import constants
from discordClient.model.models import Character, Feature, CharacterOccurrence, Affiliation, CharacterAffiliation, \
    CharactersOwnership
from discordClient.cogs import cardCogs

# The organisation is like that
#
#    #####################    #####################      #####################
#    # MENU - Categories #    # MENU - Choice     #      # MENU - Rarity     #
#    #    A - Disney     #    #    A - Rarity     #  A   #    A - Common     #
#    #    ...            # => #    B - Feature    # ===> #    B - Rary       # ==============================>|
#    #    * - All        #    #    C - Affiliation#      #    ...            #                                |
#    #####################    #    * - All        #      #    * - All        #                                |
#                             #####################      #####################                                |
#                                      |                                                                      |
#                                      |                 #####################         #####################  |
#                                      |                 # MENU - Letter     #   si    # MENU - Feature    #  |
#                                      |         B | C   #    A              # B avant #    A              # >|
#                                      |==============>  #    ...            #   ===>  #    ...            #  |     #####################
#                                      |                 #    J              #         #    J              #  |     # Affichage perso   #
#                                      |                 #####################         #####################  |     #                   #
#                                      |                          |											  |===> #                   # ==| Boucle
#                                      |                          |                    #####################  |     #                   # <=|
#                                      |                          |                    # MENU - Afiiliation#  |     #####################
#                                      |                          |     si C avant     #    A              #  |
#                                      |                          |=================>  #    ...            # >|
#                                      |                                               #    J              #  |
#                                      |                                               #####################  |
#                                      | si *                                                                 |
#                                      |=====================================================================>|


class MuseumCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")

    def retrieve_category_name(self, embeds: Embed) -> str:
        return self.retrieve_from_embed(embeds, "Category: (\w+)")

    def retrieve_offset(self, embeds: Embed) -> int:
        offset = self.retrieve_from_embed(embeds, "Offset: (\d+)")
        if offset:
            return int(offset)
        return 0

    def retrieve_letter(self, embeds: Embed) -> str:
        return self.retrieve_from_embed(embeds, "Letter: (\w+)")

    def retrieve_rarity(self, embeds: Embed) -> int:
        rarity = self.retrieve_from_embed(embeds, "Rarity: (\d+)")
        if rarity:
            return int(rarity)
        return -1

    def retrieve_origin(self, embeds: Embed) -> str:
        return self.retrieve_from_embed(embeds, "Origin: (\w+)")

    def retrieve_affiliation(self, embeds: Embed) -> str:
        return self.retrieve_from_embed(embeds, "Affiliation: (\w+)")

    ################################
    #       MODEL METHODS          #
    ################################

    def retrieve_characters_category(self):
        return Character.select(Character.category).group_by(Character.category)

    def retrieve_origins(self, category: str, letter: str):
        if category != "All":
            features = (Feature.select(Feature)
                        .join(CharacterOccurrence)
                        .join(Character)
                        .where(Feature.name.startswith(letter), Character.category == category)
                        .group_by(Feature.name, Feature.type)
                        .order_by(Feature.name.asc()))
        else:
            features = (Feature.select(Feature)
                        .where(Feature.name.startswith(letter))
                        .order_by(Feature.name.asc()))
        return features

    def retrieve_affiliations(self, category: str, letter: str):
        if category != "All":
            affiliations = (Affiliation.select(Affiliation)
                            .join(CharacterAffiliation)
                            .join(Character)
                            .where(Affiliation.name.startswith(letter),
                                   Character.category == category)
                            .group_by(Affiliation.name)
                            .order_by(Affiliation.name.asc()))
        else:
            affiliations = (Affiliation.select(Affiliation)
                            .where(Affiliation.name.startswith(letter))
                            .order_by(Affiliation.name.asc()))
        return affiliations

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command("museum")
    async def museum(self, ctx: Context):
        await self.display_menu_categories(ctx)

    @commands.command("report")
    async def report(self, ctx: Context):
        query = (Character.select(Character.name, Character.description, Character.category, Character.rarity)
                          .join(CharactersOwnership))
        df = pd.DataFrame(list(query.dicts()))
        r = dp.Report(
            dp.Markdown('My simple report'),  # add description to the report
            dp.DataTable(df),  # create a table
        )

        # Publish your report. Make sure to have visibility='PUBLIC' if you want to share your report
        r.save(path='report.html')

    ################################
    #       MENUS                  #
    ################################

    async def display_menu_categories(self, ctx: Message):
        menu_description = "Select the category you want to display\n"
        nbr_category = 0
        categories = self.retrieve_characters_category()
        for character in categories:
            menu_description += f"\n{constants.LETTER_EMOJIS[nbr_category]} **{character.category}**"
            nbr_category += 1
        menu_description += f"\n{constants.ASTERISK_EMOJI} **Display all collections**"
        category_embed = Embed(description=menu_description)
        category_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        category_embed.set_footer(text=f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_CATEGORIES']}")
        msg = await ctx.reply(embed=category_embed, delete_after=300, mention_author=False)
        index_category = 0
        while index_category < nbr_category:
            await msg.add_reaction(constants.LETTER_EMOJIS[index_category])
            index_category += 1
        await msg.add_reaction(constants.ASTERISK_EMOJI)

    async def display_menu_types(self, ctx: Message, category_selected: str):
        type_description = "Select the types you want to display\n"
        type_description += f"\n{constants.LETTER_EMOJIS[0]} **Rarities**"
        type_description += f"\n{constants.LETTER_EMOJIS[1]} **Features**"
        type_description += f"\n{constants.LETTER_EMOJIS[2]} **Affiliations**"
        type_description += f"\n{constants.ASTERISK_EMOJI} **Display all types**"
        type_embed = Embed(description=type_description)
        type_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        type_embed.set_footer(text=f"Category: {category_selected} | "
                                   f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_TYPES']}")
        msg = await ctx.reply(embed=type_embed, delete_after=300, mention_author=False)
        await msg.add_reaction(constants.LETTER_EMOJIS[0])
        await msg.add_reaction(constants.LETTER_EMOJIS[1])
        await msg.add_reaction(constants.LETTER_EMOJIS[2])
        await msg.add_reaction(constants.ASTERISK_EMOJI)

    async def display_menu_rarities(self, ctx: Message, category_selected: str):
        rarity_description = "Select the rarities you want to display\n"
        label_index = 0
        for rarity_emoji in constants.RARITIES_EMOJI:
            #rarity_description += f"\n{rarity_emoji} **{constants.RARITIES_LABELS[label_index]}**"
            rarity_description += f"\n{rarity_emoji} **{constants.RARITIES_LABELS[label_index]}**"
            label_index += 1
        rarity_description += f"\n{constants.ASTERISK_EMOJI} **Display all rarities**"
        rarity_embed = Embed(description=rarity_description)
        rarity_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        rarity_embed.set_footer(text=f"Category: {category_selected} | "
                                     f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_RARITIES']}")
        msg = await ctx.reply(embed=rarity_embed, delete_after=300, mention_author=False)
        for rarity_emoji in constants.RARITIES_EMOJI:
            await msg.add_reaction(rarity_emoji)
        await msg.add_reaction(constants.ASTERISK_EMOJI)

    async def display_menu_letters(self, ctx: Message, category_selected: str, puppet_id: int, letters_offset: int = 0):
        letters_description = "Select the first letter you want to display\n"
        letters_embed = Embed(description=letters_description)
        letters_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        letters_embed.set_footer(text=f"Category: {category_selected} | Offset: {letters_offset} | "
                                      f"Puppet_id: {str(puppet_id)}")
        msg = await ctx.reply(embed=letters_embed, delete_after=300, mention_author=False)
        if letters_offset > 0:
            await msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        for _ in range(0, 10):
            letter_index = _ + (letters_offset * 10)
            if letter_index < 26:
                await msg.add_reaction(constants.LETTER_EMOJIS[letter_index])
        if letters_offset < 2:
            await msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

    async def display_menu_origins(self, ctx: Message, category_selected: str, letter: str, offset: int = 0):
        features = self.retrieve_origins(category_selected, letter)
        feature_description = "Select the feature collection you want to display\n"

        for _ in range(0, 10):
            feature_index = _ + (offset * 10)
            if feature_index < len(features):
                feature_description += f"\n{constants.LETTER_EMOJIS[_]} **{features[feature_index].name}** - " \
                                       f"{features[feature_index].type.upper()}"
            else:
                break

        features_embed = Embed(description=feature_description)
        features_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        features_embed.set_footer(text=f"Category: {category_selected} | "
                                       f"Letter: {letter} | Offset: {offset} | "
                                       f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_ORIGINS']}")
        msg = await ctx.reply(embed=features_embed, delete_after=300, mention_author=False)
        if offset > 0:
            await msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        for _ in range(0, 10):
            feature_index = _ + (offset * 10)
            if feature_index < len(features):
                await msg.add_reaction(constants.LETTER_EMOJIS[_])
            else:
                break
        if offset < math.ceil(len(features) / 10) - 1:
            await msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

    async def display_menu_affiliations(self, ctx: Message, category_selected: str, letter: str, offset: int = 0):
        affiliations = self.retrieve_affiliations(category_selected, letter)
        affiliation_description = "Select the affiliation collection you want to display\n"

        for _ in range(0, 10):
            affiliation_index = _ + (offset * 10)
            if affiliation_index < len(affiliations):
                affiliation_description += f"\n{constants.LETTER_EMOJIS[_]} **{affiliations[affiliation_index].name}**"
            else:
                break

        affiliations_embed = Embed(description=affiliation_description)
        affiliations_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        affiliations_embed.set_footer(text=f"Category: {category_selected} | "
                                           f"Letter: {letter} | Offset: {offset} |"
                                           f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_AFFILIATIONS']}")
        msg = await ctx.reply(embed=affiliations_embed, delete_after=300, mention_author=False)
        if offset > 0:
            await msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        for _ in range(0, 10):
            affiliation_index = _ + (offset * 10)
            if affiliation_index < len(affiliations):
                await msg.add_reaction(constants.LETTER_EMOJIS[_])
            else:
                break
        if offset < math.ceil(len(affiliations) / 10) - 1:
            await msg.add_reaction(constants.RIGHT_ARROW_EMOJI)
        pass

    async def display_characters(self, ctx: Message, category_selected, user_id: int, rarity: int = -1,
                                 origin: str = "", affiliation: str = "", offset: int = 0):
        # Characters retrieving
        query = Character.select(Character)
        if category_selected != "All":
            query = query.where(Character.category == category_selected)
        if rarity >= 0:
            query = query.where(Character.rarity == rarity)
        if origin:
            query = (query.join(CharacterOccurrence)
                          .join(Feature)
                          .where(Feature.name == origin))
        if affiliation:
            query = (query.join(CharacterAffiliation)
                          .join(Affiliation)
                          .where(Affiliation.name == affiliation))
        total_characters = query.count()

        # Then we filter on only the owned card
        query = (query.join(CharactersOwnership)
                      .where(CharactersOwnership.discord_user_id == user_id)
                      .order_by(Character.name))

        total_owned = query.count()

        for character in query.paginate(offset + 1, 10):
            character_embed = cardCogs.generate_embed_character(character)
            msg = await ctx.reply(embed=character_embed, delete_after=300, mention_author=False)
            await msg.add_reaction('💰')

        end_page = math.ceil(total_owned / 10)
        page_index = offset + 1
        page_embed = Embed(description=f"You currently own {total_owned}/{total_characters} characters.",
                           title=f"Page {page_index}/{end_page}")
        footer = f'Category: {category_selected}'
        if rarity != -1:
            footer += f' | Rarity: {rarity}'
        if origin:
            footer += f' | Origin: {origin}'
        if affiliation:
            footer += f' | Affiliation: {affiliation}'
        footer += f' | Offset: {offset} | Puppet_id: {constants.PUPPET_IDS["MUSEUM_COGS_CHARACTERS"]}'
        page_embed.set_footer(text=footer)
        page_msg = await ctx.reply(embed=page_embed, delete_after=300, mention_author=False)
        if offset > 0:
            await page_msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        if (offset + 1) * 10 < total_owned:
            await page_msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

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
        if puppet_id in [constants.PUPPET_IDS["MUSEUM_COGS_CATEGORIES"], constants.PUPPET_IDS["MUSEUM_COGS_TYPES"],
                         constants.PUPPET_IDS["MUSEUM_COGS_ORIGIN_LETTERS"],
                         constants.PUPPET_IDS["MUSEUM_COGS_ORIGINS"],
                         constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"],
                         constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATIONS"],
                         constants.PUPPET_IDS["MUSEUM_COGS_RARITIES"],
                         constants.PUPPET_IDS["MUSEUM_COGS_CHARACTERS"]]:
            category = self.retrieve_category_name(origin_message.embeds)

            # Categories => Choice
            if puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_CATEGORIES"]:
                if payload.emoji.name == constants.ASTERISK_EMOJI:
                    await self.display_menu_types(replied_message, "All")
                else:
                    # Il faudra gérer une exception ValueError ici
                    index_category = constants.LETTER_EMOJIS.index(payload.emoji.name)
                    category = self.retrieve_characters_category()[index_category].category
                    await self.display_menu_types(replied_message, category)

            # Choice => si A => Rarities
            #        => si B ou C => Affichage d'un menu de première lettre
            #        => sinon => Affichage des personnages
            elif puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_TYPES"]:
                if payload.emoji.name == constants.LETTER_EMOJIS[0]:  # A - Rarities
                    await self.display_menu_rarities(replied_message, category)
                elif payload.emoji.name == constants.LETTER_EMOJIS[1]:  # B - Feature
                    await self.display_menu_letters(replied_message, category,
                                                    constants.PUPPET_IDS["MUSEUM_COGS_ORIGIN_LETTERS"])
                elif payload.emoji.name == constants.LETTER_EMOJIS[2]:  # C - Affiliations
                    await self.display_menu_letters(replied_message, category,
                                                    constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"])
                else:  # * - All
                    await self.display_characters(replied_message, category, payload.user_id)
                    pass

            # Letter => si FLECHE_GAUCHE => Letter (offset - 1)
            #        => si FLECHE_DROITE => Letter (offset + 1)
            #        => si LETTRE => si puppet_id == MUSEUM_COGS_ORIGIN_LETTERS => Feature
            #                     => si puppet_id == MUSEUM_COGS_AFFILIATION_LETTERS => Affiliation
            elif (puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_ORIGIN_LETTERS"] or
                  puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"]):
                current_offset = self.retrieve_offset(origin_message.embeds)
                if payload.emoji.name == constants.LEFT_ARROW_EMOJI:
                    current_offset -= 1
                elif payload.emoji.name == constants.RIGHT_ARROW_EMOJI:
                    current_offset += 1
                elif payload.emoji.name in constants.LETTER_EMOJIS:
                    letter_index = constants.LETTER_EMOJIS.index(payload.emoji.name) + 65
                    if puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_ORIGIN_LETTERS"]:
                        await self.display_menu_origins(replied_message, category, str(chr(letter_index)))
                    else:
                        await self.display_menu_affiliations(replied_message, category, str(chr(letter_index)))
                    return
                await self.display_menu_letters(replied_message, category, puppet_id, current_offset)

            # Origins => si FLECHE_GAUCHE => Origins (offset - 1)
            #         => si FLECHE_DROITE => Origins (offset + 1)
            #         => si LETTRE => Affichage des personnages
            elif puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_ORIGINS"]:
                current_offset = self.retrieve_offset(origin_message.embeds)
                current_letter = self.retrieve_letter(origin_message.embeds)
                if payload.emoji.name == constants.LEFT_ARROW_EMOJI:
                    current_offset -= 1
                elif payload.emoji.name == constants.RIGHT_ARROW_EMOJI:
                    current_offset += 1
                elif payload.emoji.name in constants.LETTER_EMOJIS:
                    origins = self.retrieve_origins(category, current_letter)
                    index_origin_selected = constants.LETTER_EMOJIS.index(payload.emoji.name)
                    index_origin_selected += (current_offset * 10)
                    await self.display_characters(replied_message, category,
                                                  origins=origins[index_origin_selected].name)
                    return
                await self.display_menu_origins(replied_message, category, current_letter, current_offset)

            # Affiliation => si FLECHE_GAUCHE => Affiliation (offset - 1)
            #             => si FLECHE_DROITE => Affiliation (offset + 1)
            #             => si LETTRE => Affichage des personnages
            elif puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATIONS"]:
                current_offset = self.retrieve_offset(origin_message.embeds)
                current_letter = self.retrieve_letter(origin_message.embeds)
                if payload.emoji.name == constants.LEFT_ARROW_EMOJI:
                    current_offset -= 1
                elif payload.emoji.name == constants.RIGHT_ARROW_EMOJI:
                    current_offset += 1
                elif payload.emoji.name in constants.LETTER_EMOJIS:
                    affiliations = self.retrieve_affiliations(category, current_letter)
                    index_affiliation_selected = constants.LETTER_EMOJIS.index(payload.emoji.name)
                    index_affiliation_selected += (current_offset * 10)
                    await self.display_characters(replied_message, category, payload.user_id,
                                                  affiliations=affiliations[index_affiliation_selected].name)
                    return
                await self.display_menu_affiliations(replied_message, category, current_letter, current_offset)

            # Rarities => Affichage des personnages
            elif puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_RARITIES"]:
                #if payload.emoji.name in constants.RARITIES_EMOJI:
                if str(payload.emoji) in constants.RARITIES_EMOJI:
                    #index_rarity = constants.RARITIES_EMOJI.index(payload.emoji.name)
                    index_rarity = constants.RARITIES_EMOJI.index(str(payload.emoji))
                    await self.display_characters(replied_message, category, payload.user_id, index_rarity)
                elif payload.emoji.name == constants.ASTERISK_EMOJI:
                    await self.display_characters(replied_message, category, payload.user_id)

            elif puppet_id == constants.PUPPET_IDS["MUSEUM_COGS_CHARACTERS"]:
                current_offset = self.retrieve_offset(origin_message.embeds)
                current_rarity = self.retrieve_rarity(origin_message.embeds)
                current_affiliation = self.retrieve_affiliation(origin_message.embeds)
                current_origin = self.retrieve_origin(origin_message.embeds)
                if payload.emoji.name == constants.LEFT_ARROW_EMOJI:
                    current_offset -= 1
                elif payload.emoji.name == constants.RIGHT_ARROW_EMOJI:
                    current_offset += 1
                await self.display_characters(replied_message, category, payload.user_id, current_rarity,
                                              current_origin, current_affiliation, current_offset)
