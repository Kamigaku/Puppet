import math
# import datapane as dp
# import pandas as pd
from peewee import fn
from discord import Embed, Message, User, Emoji, DMChannel
from discord.ext import commands
from discord.ext.commands import Context
from discordClient.cogs.abstract import assignableCogs
from discordClient.cogs import cardCogs
from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener
from discordClient.model.models import Character, Affiliation, CharacterAffiliation, \
    CharactersOwnership

# The organisation is like that
#
#    #####################    #####################      #####################
#    # MENU - Categories #    # MENU - Choice     #      # MENU - Rarity     #
#    #    A - Disney     #    #    A - Rarity     #  A   #    A - Common     #
#    #    ...            # => #    B - Affiliation# ===> #    B - Rary       # ==============================>|
#    #    * - All      1 #    #    * - All      2 #      #    ...            #                                |
#    #####################    #####################      #    * - All      3 #                                |
#                                      |                 #####################                                |
#                                      |                                                                      |
#                                      |                 #####################         #####################  |
#                                      |                 # MENU - Letter     #   si    # MENU - Feature    #  |
#                                      |         B       #    A              # B avant #    A              # >|
#                                      |==============>  #    ...            #   ===>  #    ...            #  |
#                                      |                 #    J            4 #         #    J            5 #  |
#                                      |                 #####################         #####################  |
#                                      |                                                                      |
#                                      |                                                            v=========|
#                                      |                                                 #####################
#                                      | si *                                            # Affichage perso   #
#                                      |================================================>#                   #
#                                                                                        #                   # ==| Loop
#                                                                                        #                 6 # <=|
#                                                                                        #####################
#


class MuseumCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "museum")
        self.enable()

    def enable(self):
        categories_emojis = constants.LETTER_EMOJIS.copy()
        categories_emojis.append(constants.ASTERISK_EMOJI)
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  categories_emojis,
                                                  self.menu_categories_to_choice,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_CATEGORIES"],
                                                  return_emoji=True))
        types_emojis = [constants.LETTER_EMOJIS[0], constants.LETTER_EMOJIS[1], constants.ASTERISK_EMOJI]
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  types_emojis,
                                                  self.menu_choices_to_path,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_TYPES"],
                                                  return_emoji=True))
        affiliations_emojis = constants.LETTER_EMOJIS.copy()
        affiliations_emojis.append(constants.LEFT_ARROW_EMOJI)
        affiliations_emojis.append(constants.RIGHT_ARROW_EMOJI)
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  affiliations_emojis,
                                                  self.menu_letters_to_path,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"],
                                                  return_emoji=True))
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  affiliations_emojis,
                                                  self.menu_affiliations_to_path,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATIONS"],
                                                  return_emoji=True))
        rarities_emojis = constants.RARITIES_EMOJI.copy()
        rarities_emojis.append(constants.ASTERISK_EMOJI)
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  rarities_emojis,
                                                  self.menu_rarities_to_character,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_RARITIES"],
                                                  return_emoji=True))
        characters_emojis = constants.NUMBER_EMOJIS[1:].copy()
        characters_emojis.append(constants.LEFT_ARROW_EMOJI)
        characters_emojis.append(constants.RIGHT_ARROW_EMOJI)
        self.bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                  characters_emojis,
                                                  self.menu_characters_to_next_page,
                                                  constants.PUPPET_IDS["MUSEUM_COGS_CHARACTERS"],
                                                  return_emoji=True))

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

    def retrieve_affiliation(self, embeds: Embed) -> str:
        return self.retrieve_from_embed(embeds, "Affiliation: (\w+)")

    ################################
    #       MODEL METHODS          #
    ################################

    def retrieve_characters_category(self):
        return Character.select(Character.category).group_by(Character.category)

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
    #       CALLBACKS              #
    ################################

    # Menu #2
    async def menu_categories_to_choice(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            if emoji.name == constants.ASTERISK_EMOJI:
                await self.display_menu_types(origin_message, "All")
            else:
                index_category = constants.LETTER_EMOJIS.index(emoji.name)
                category = self.retrieve_characters_category()[index_category].category
                await self.display_menu_types(origin_message, category)
            self.unregister_locked_message(origin_message.id)

    # Menu #3 and #4
    async def menu_choices_to_path(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            category = self.retrieve_category_name(origin_message.embeds)
            if emoji.name == constants.LETTER_EMOJIS[0]:  # A - Rarities
                await self.display_menu_rarities(origin_message, category)
            elif emoji.name == constants.LETTER_EMOJIS[1]:  # B - Affiliation
                await self.display_menu_letters(origin_message, category,
                                                constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"])
            else:  # * - All
                await self.display_characters(origin_message, category, user_that_reacted)
            self.unregister_locked_message(origin_message.id)

    # Menu #4
    async def menu_letters_to_path(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            category = self.retrieve_category_name(origin_message.embeds)
            current_offset = self.retrieve_offset(origin_message.embeds)
            if emoji.name == constants.LEFT_ARROW_EMOJI:
                current_offset -= 1
            elif emoji.name == constants.RIGHT_ARROW_EMOJI:
                current_offset += 1
            elif emoji.name in constants.LETTER_EMOJIS:
                letter_index = constants.LETTER_EMOJIS.index(emoji.name) + 65
                await self.display_menu_affiliations(origin_message, category, str(chr(letter_index)))
                return
            await self.display_menu_letters(origin_message, category,
                                            constants.PUPPET_IDS["MUSEUM_COGS_AFFILIATION_LETTERS"], current_offset)
            self.unregister_locked_message(origin_message.id)

    # Menu #5
    async def menu_affiliations_to_path(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            category = self.retrieve_category_name(origin_message.embeds)
            current_offset = self.retrieve_offset(origin_message.embeds)
            current_letter = self.retrieve_letter(origin_message.embeds)
            if emoji.name == constants.LEFT_ARROW_EMOJI:
                current_offset -= 1
            elif emoji.name == constants.RIGHT_ARROW_EMOJI:
                current_offset += 1
            elif emoji.name in constants.LETTER_EMOJIS:
                affiliations = self.retrieve_affiliations(category, current_letter)
                index_affiliation_selected = constants.LETTER_EMOJIS.index(emoji.name)
                index_affiliation_selected += (current_offset * 10)
                await self.display_characters(origin_message, category, user_that_reacted,
                                              affiliation=affiliations[index_affiliation_selected].name)
                return
            await self.display_menu_affiliations(origin_message, category, current_letter, current_offset)
            self.unregister_locked_message(origin_message.id)

    # Menu #4
    async def menu_rarities_to_character(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            category = self.retrieve_category_name(origin_message.embeds)
            if str(emoji) in constants.RARITIES_EMOJI:
                index_rarity = constants.RARITIES_EMOJI.index(str(emoji))
                await self.display_characters(origin_message, category, user_that_reacted, index_rarity)
            elif emoji.name == constants.ASTERISK_EMOJI:
                await self.display_characters(origin_message, category, user_that_reacted)
            self.unregister_locked_message(origin_message.id)

    # Menu #6
    async def menu_characters_to_next_page(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        self.register_locked_message(origin_message.id)
        async with self.locked_message[origin_message.id]["lock"]:
            category = self.retrieve_category_name(origin_message.embeds)
            current_offset = self.retrieve_offset(origin_message.embeds)
            current_rarity = self.retrieve_rarity(origin_message.embeds)
            current_affiliation = self.retrieve_affiliation(origin_message.embeds)
            if emoji.name in [constants.LEFT_ARROW_EMOJI, constants.RIGHT_ARROW_EMOJI]:
                if emoji.name == constants.LEFT_ARROW_EMOJI:
                    current_offset -= 1
                elif emoji.name == constants.RIGHT_ARROW_EMOJI:
                    current_offset += 1
                await self.display_characters(origin_message, category, user_that_reacted, current_rarity,
                                              current_affiliation, current_offset, False)
            else: # We want to display a player
                character_index = constants.NUMBER_EMOJIS.index(emoji.name) - 1
                await self.display_character(origin_message, category, user_that_reacted, current_rarity,
                                             current_affiliation, current_offset, character_index)
                pass

            self.unregister_locked_message(origin_message.id)

    ################################
    #       MENUS                  #
    ################################

    async def display_menu_categories(self, ctx: Context):
        menu_description = "Select the category you want to display\n"
        nbr_category = 0
        categories = self.retrieve_characters_category()
        for character in categories:
            menu_description += f"\n{constants.LETTER_EMOJIS[nbr_category]} **{character.category}**"
            nbr_category += 1
        menu_description += f"\n{constants.ASTERISK_EMOJI} **Display all collections**"
        category_embed = Embed(description=menu_description)
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
        type_description += f"\n{constants.LETTER_EMOJIS[1]} **Affiliations**"
        type_description += f"\n{constants.ASTERISK_EMOJI} **Display all types**"
        type_embed = Embed(description=type_description)
        type_embed.set_footer(text=f"Category: {category_selected} | "
                                   f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_TYPES']}")
        if type(ctx.channel) == DMChannel:
            msg = await ctx.reply(embed=type_embed, delete_after=300, mention_author=False)
        else:
            await ctx.clear_reactions()
            await ctx.edit(embed=type_embed, delete_after=300, mention_author=False)
            msg = ctx
        await msg.add_reaction(constants.LETTER_EMOJIS[0])
        await msg.add_reaction(constants.LETTER_EMOJIS[1])
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
        rarity_embed.set_footer(text=f"Category: {category_selected} | "
                                     f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_RARITIES']}")
        if type(ctx.channel) == DMChannel:
            msg = await ctx.reply(embed=rarity_embed, delete_after=300, mention_author=False)
        else:
            await ctx.clear_reactions()
            await ctx.edit(embed=rarity_embed, delete_after=300, mention_author=False)
            msg = ctx
        for rarity_emoji in constants.RARITIES_EMOJI:
            await msg.add_reaction(rarity_emoji)
        await msg.add_reaction(constants.ASTERISK_EMOJI)

    async def display_menu_letters(self, ctx: Message, category_selected: str, puppet_id: int, letters_offset: int = 0):
        letters_description = "Select the first letter you want to display\n"
        letters_embed = Embed(description=letters_description)
        letters_embed.set_footer(text=f"Category: {category_selected} | Offset: {letters_offset} | "
                                      f"Puppet_id: {str(puppet_id)}")
        if type(ctx.channel) == DMChannel:
            msg = await ctx.reply(embed=letters_embed, delete_after=300, mention_author=False)
        else:
            await ctx.clear_reactions()
            await ctx.edit(embed=letters_embed, delete_after=300, mention_author=False)
            msg = ctx
        if letters_offset > 0:
            await msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        for _ in range(0, 10):
            letter_index = _ + (letters_offset * 10)
            if letter_index < 26:
                await msg.add_reaction(constants.LETTER_EMOJIS[letter_index])
        if letters_offset < 2:
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
        affiliations_embed.set_footer(text=f"Category: {category_selected} | "
                                           f"Letter: {letter} | Offset: {offset} |"
                                           f"Puppet_id: {constants.PUPPET_IDS['MUSEUM_COGS_AFFILIATIONS']}")
        if type(ctx.channel) == DMChannel:
            msg = await ctx.reply(embed=affiliations_embed, delete_after=300, mention_author=False)
        else:
            await ctx.clear_reactions()
            await ctx.edit(embed=affiliations_embed, delete_after=300, mention_author=False)
            msg = ctx
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

    async def display_characters(self, ctx: Message, category_selected, user: User, rarity: int = -1,
                                 affiliation: str = "", offset: int = 0, first_iteration: bool = True):
        # Characters retrieving
        query = Character.select(Character, fn.Count(Character.id).alias('count'))
        if category_selected != "All":
            query = query.where(Character.category == category_selected)
        if rarity >= 0:
            query = query.where(Character.rarity == rarity)
        if affiliation:
            query = (query.join(CharacterAffiliation)
                          .join(Affiliation)
                          .where(Affiliation.name == affiliation))
        total_characters = query.count()

        # Then we filter on only the owned card
        query = (query.join(CharactersOwnership, on=(CharactersOwnership.character_id == Character.id))
                      .where(CharactersOwnership.discord_user_id == user.id)
                      .group_by(Character.id)
                      .order_by(Character.name))

        total_owned = query.count()

        if offset * 10 > total_owned or offset < 0:
            return

        characters_embed = Embed(title="Character collection")
        characters_embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        index = 1
        for character in query.paginate(offset + 1, 10):
            affiliations = (Affiliation.select(Affiliation.name)
                                       .join(CharacterAffiliation)
                                       .where(CharacterAffiliation.character_id == character.id))
            affiliation_text = ""
            for character_affiliation in affiliations:
                affiliation_text += f"{character_affiliation.name}, "
            character_field = f"`{index}.` {constants.RARITIES_EMOJI[character.rarity]} " \
                              f"[{constants.RARITIES_LABELS[character.rarity]}] {character.name}"
            if character.count > 1:
                character_field += f" (x{character.count})"
            characters_embed.add_field(name=character_field, value=f"{affiliation_text[:-2]}", inline=False)
            index += 1

        end_page = math.ceil(total_owned / 10)
        page_index = offset + 1
        page_message = f"Page #{page_index}/{end_page} | You currently own {total_owned}/{total_characters} " \
                       f"characters."
        footer = f'Category: {category_selected}'
        if rarity != -1:
            footer += f' | Rarity: {rarity}'
        if affiliation:
            footer += f' | Affiliation: {affiliation}'
        footer += f' | Offset: {offset} | Puppet_id: {constants.PUPPET_IDS["MUSEUM_COGS_CHARACTERS"]}'
        characters_embed.set_footer(text=footer)
        if type(ctx.channel) == DMChannel:
            msg = await ctx.reply(content=page_message, embed=characters_embed, delete_after=300, mention_author=False)
        else:
            await ctx.edit(content=page_message, embed=characters_embed, delete_after=300, mention_author=False)
            msg = ctx

        if first_iteration:
            if type(ctx.channel) is not DMChannel:
                await ctx.clear_reactions()
            await msg.add_reaction(constants.LEFT_ARROW_EMOJI)
            numbers = constants.NUMBER_EMOJIS[1:]
            for number in numbers:
                await msg.add_reaction(number)
            await msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

    # A factoriser avec display_characters
    async def display_character(self, ctx: Message, category_selected, user: User, rarity: int = -1,
                                affiliation: str = "", offset: int = 0, character_offset: int = 0):
        # Characters retrieving
        query = Character.select(Character)
        if category_selected != "All":
            query = query.where(Character.category == category_selected)
        if rarity >= 0:
            query = query.where(Character.rarity == rarity)
        if affiliation:
            query = (query.join(CharacterAffiliation)
                     .join(Affiliation)
                     .where(Affiliation.name == affiliation))

        # Then we filter on only the owned card
        query = (query.join(CharactersOwnership, on=(CharactersOwnership.character_id == Character.id))
                 .where(CharactersOwnership.discord_user_id == user.id)
                 .order_by(Character.name))
        characters = query.paginate(offset + 1, 10)
        embed = cardCogs.generate_embed_character(characters[character_offset])
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction(constants.SELL_EMOJI)
        await msg.add_reaction(constants.REPORT_EMOJI)



