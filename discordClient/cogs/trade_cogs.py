import hashlib

from discord import User, Embed, Message, Emoji, utils
from discord.ext import commands
from discord.ext.commands import Context

from discordClient.cogs.abstract import assignableCogs
from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener
from discordClient.model.models import Affiliation, CharacterAffiliation, CharactersOwnership, Character, Trade


class TradeCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "trade")
        self.enable()

    def enable(self):
        add_remove_reactions = [constants.REACTION_ADD, constants.REACTION_REMOVE]
        arrow_emojis = [constants.LEFT_ARROW_EMOJI, constants.RIGHT_ARROW_EMOJI]

        self.bot.append_listener(ReactionListener(add_remove_reactions,
                                                  arrow_emojis,
                                                  self.iterate_next_characters,
                                                  constants.PUPPET_IDS["TRADE_COGS_LIST"],
                                                  return_emoji=True))
        number_emojis = constants.NUMBER_EMOJIS[1:].copy()
        self.bot.append_listener(ReactionListener(add_remove_reactions,
                                                  number_emojis,
                                                  self.add_or_remove_item,
                                                  constants.PUPPET_IDS["TRADE_COGS_LIST"],
                                                  return_emoji=True))
        self.bot.append_listener(ReactionListener(add_remove_reactions,
                                                  constants.RED_CROSS_EMOJI,
                                                  self.applicant_cancel_trade,
                                                  constants.PUPPET_IDS["TRADE_COGS_LIST"]))
        self.bot.append_listener(ReactionListener(add_remove_reactions,
                                                  constants.CHECK_EMOJI,
                                                  self.applicant_validate_trade,
                                                  constants.PUPPET_IDS["TRADE_COGS_LIST"]))
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.RED_CROSS_EMOJI,
                                                  self.applicant_cancel_confirm,
                                                  constants.PUPPET_IDS["TRADE_COGS_RECAP"]))
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.CHECK_EMOJI,
                                                  self.applicant_confirm,
                                                  constants.PUPPET_IDS["TRADE_COGS_RECAP"]))
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.RED_CROSS_EMOJI,
                                                  self.refuse_trade,
                                                  constants.PUPPET_IDS["TRADE_COGS_OFFER"]))
        self.bot.append_listener(ReactionListener(constants.REACTION_ADD,
                                                  constants.CHECK_EMOJI,
                                                  self.accept_trade,
                                                  constants.PUPPET_IDS["TRADE_COGS_OFFER"]))

    def retrieve_trade_id(self, embeds: Embed) -> int:
        trade_id = self.retrieve_from_embed(embeds, "Trade_id: (\d+)")
        if trade_id:
            return int(trade_id)
        return 0

    def retrieve_page(self, embeds: Embed) -> int:
        page = self.retrieve_from_embed(embeds, "Page: (\d+)")
        if page:
            return int(page)
        return 0

    def retrieve_selected_chars(self, embed: Embed):
        selected_chars = {}
        for field in embed.fields:
            selected_chars[field.name] = []
            if field.value == "None":
                continue
            selected_chars[field.name].extend(field.value.split("\n"))
        return selected_chars

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command(name="trade")
    async def trade(self, ctx: Context, discord_user: User):
        if discord_user.id == ctx.author.id:
            await ctx.author.send("You cannot trade with yourself.")

        header_embed = self.generate_header_trade(ctx.author, discord_user, [], [])
        header_msg = await ctx.reply(content=f"Trade between {ctx.author.mention} and {discord_user.mention}",
                                     embed=header_embed)

        query = (Character.select(Character)
                          .join(CharactersOwnership)
                          .where(CharactersOwnership.discord_user_id == ctx.author.id)
                          .order_by(Character.rarity.desc())).paginate(1, 10)

        content_embed = self.generate_content_trade(query, ctx.author)
        content_msg = await header_msg.reply(embed=content_embed)
        await content_msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        for _ in range(1, 11):
            await content_msg.add_reaction(constants.NUMBER_EMOJIS[_])
        await content_msg.add_reaction(constants.RIGHT_ARROW_EMOJI)
        await content_msg.add_reaction(constants.RED_CROSS_EMOJI)
        await content_msg.add_reaction(constants.CHECK_EMOJI)

    ################################
    #       MENUS                  #
    ################################

    def generate_header_trade(self, applicant: User, recipient: User, applicant_chars: list, recipient_chars: list):
        embed_header = Embed()
        embed_header.title = "Trade recap"
        embed_header.description = f"The section list the traded cards between " \
                                   f"**{applicant.name}#{applicant.discriminator}** and " \
                                   f"**{recipient.name}#{recipient.discriminator}**"
        embed_header.set_author(name=f"{applicant.name}#{applicant.discriminator}", icon_url=applicant.avatar_url)
        embed_header.set_thumbnail(url=recipient.avatar_url)

        value_applicant = "\n".join(applicant_chars)
        if not value_applicant:
            value_applicant = "None"
        value_recipient = "\n".join(recipient_chars)
        if not value_recipient:
            value_recipient = "None"

        embed_header.add_field(name=f"{applicant.name}#{applicant.discriminator}", value=value_applicant)
        embed_header.add_field(name=f"{recipient.name}#{recipient.discriminator}", value=value_recipient)
        embed_header.set_footer(text=f"Puppet_id: {constants.PUPPET_IDS['TRADE_COGS_RECAP']}")
        return embed_header

    def generate_content_trade(self, characters: list, owner: User, offset: int = 1):
        list_embed = Embed()
        list_embed.set_author(name=f"{owner.name}#{owner.discriminator}", icon_url=owner.avatar_url)
        list_embed.title = "Summary of owned characters"
        iteration = 1
        description = ""
        for character in characters:
            description += f"`{iteration}.` {constants.RARITIES_EMOJI[character.rarity]} " \
                           f"[**{constants.RARITIES_LABELS[character.rarity]}**] {character.name}\n"
            affiliations = (Affiliation.select(Affiliation.name)
                            .join(CharacterAffiliation)
                            .where(CharacterAffiliation.character_id == character.id))
            affiliation_text = ""
            for character_affiliation in affiliations:
                affiliation_text += f"{character_affiliation.name}, "
            description += f"{affiliation_text[:-2]}\n"
            iteration += 1
        if not description:
            description = "This user has no character."
        list_embed.description = description
        footer = f"Page: {offset} | Puppet_id: {constants.PUPPET_IDS['TRADE_COGS_LIST']}"
        list_embed.set_footer(text=footer)
        return list_embed

    async def generate_trade_offer(self, trade: Trade):
        applicant = await self.retrieve_member(trade.applicant)
        recipient = await self.retrieve_member(trade.recipient)

        applicant_cards = trade.applicant_cards.split("-")
        recipient_cards = trade.recipient_cards.split("-")

        query_applicant = (Character.select(Character, CharactersOwnership.id.alias("id_own"))
                                    .join(CharactersOwnership)
                                    .where(CharactersOwnership.id << applicant_cards))
        query_recipient = (Character.select(Character, CharactersOwnership.id.alias("id_own"))
                                    .join(CharactersOwnership)
                                    .where(CharactersOwnership.id << recipient_cards))

        applicant_chars = []
        for applicant_card in query_applicant:
            applicant_chars.append(f"{applicant_card.charactersownership.id_own} • "
                                   f"{constants.RARITIES_EMOJI[applicant_card.rarity]} "
                                   f"[**{constants.RARITIES_LABELS[applicant_card.rarity]}**] {applicant_card.name}")

        recipient_chars = []
        for recipient_card in query_recipient:
            applicant_chars.append(f"{recipient_card.charactersownership.id_own} • "
                                   f"{constants.RARITIES_EMOJI[recipient_card.rarity]} "
                                   f"[**{constants.RARITIES_LABELS[recipient_card.rarity]}**] {recipient_card.name}")

        embed_trade = Embed()
        embed_trade.title = "Trade recap"
        embed_trade.description = f"This section recap the trade offer between " \
                                  f"**{applicant.name}#{applicant.discriminator}** and " \
                                  f"**{recipient.name}#{recipient.discriminator}**"
        embed_trade.set_author(name=f"{applicant.name}#{applicant.discriminator}", icon_url=applicant.avatar_url)
        embed_trade.set_thumbnail(url=recipient.avatar_url)

        value_applicant = "\n".join(applicant_chars)
        if not value_applicant:
            value_applicant = "None"
        value_recipient = "\n".join(recipient_chars)
        if not value_recipient:
            value_recipient = "None"

        embed_trade.add_field(name=f"{applicant.name}#{applicant.discriminator}", value=value_applicant)
        embed_trade.add_field(name=f"{recipient.name}#{recipient.discriminator}", value=value_recipient)
        embed_trade.set_footer(text=f"Trade_id: {trade.id} | Puppet_id: {constants.PUPPET_IDS['TRADE_COGS_OFFER']}")
        return embed_trade

    ################################
    #       CALLBACKS              #
    ################################

    async def iterate_next_characters(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        author_name = origin_message.reference.resolved.embeds[0].author.name
        if author_name != f"{user_that_reacted.name}#{user_that_reacted.discriminator}":
            return

        author_embed = origin_message.embeds[0].author.name.split("#")
        current_user = utils.get(self.bot.get_all_members(), name=author_embed[0], discriminator=author_embed[1])
        current_page = self.retrieve_page(origin_message.embeds)

        if emoji.name == constants.LEFT_ARROW_EMOJI:
            current_page -= 1
        elif emoji.name == constants.RIGHT_ARROW_EMOJI:
            current_page += 1

        if current_page < 1:
            return

        query = (Character.select(Character)
                 .join(CharactersOwnership)
                 .where(CharactersOwnership.discord_user_id == current_user.id)
                 .order_by(Character.rarity.desc()))

        if (current_page - 1) * 10 >= len(query):
            return

        paginated_character = query.paginate(current_page, 10)
        content_embed = self.generate_content_trade(paginated_character, current_user, current_page)
        await origin_message.edit(embed=content_embed)

    # Cette méthode est un peu le bazar, il faudrait la réorganiser
    async def add_or_remove_item(self, origin_message: Message, user_that_reacted: User, emoji: Emoji):
        author_name = origin_message.reference.resolved.embeds[0].author.name
        if author_name != f"{user_that_reacted.name}#{user_that_reacted.discriminator}":
            return
        author_embed = origin_message.embeds[0].author.name.split("#")
        current_user = utils.get(self.bot.get_all_members(), name=author_embed[0], discriminator=author_embed[1])
        current_page = self.retrieve_page(origin_message.embeds)
        current_index = constants.NUMBER_EMOJIS.index(emoji.name)
        query = (Character.select(Character, CharactersOwnership.id.alias("id_own"))
                 .join(CharactersOwnership)
                 .where(CharactersOwnership.discord_user_id == current_user.id)
                 .order_by(Character.rarity.desc()))
        if current_page * 10 + current_index > len(query):
            return
        paginated_character = query.paginate(current_page, 10)
        item_selected = paginated_character[current_index - 1]
        selected_chars = self.retrieve_selected_chars(origin_message.reference.resolved.embeds[0])

        id_found = False
        id_item = str(item_selected.charactersownership.id_own)
        for character in selected_chars[f"{current_user.name}#{current_user.discriminator}"]:
            character_id = character.split("•")[0].strip()
            if character_id == id_item:
                selected_chars[f"{current_user.name}#{current_user.discriminator}"].remove(character)
                id_found = True
                break

        if not id_found:
            selected_chars[f"{current_user.name}#{current_user.discriminator}"].append(
                f"{id_item} • {constants.RARITIES_EMOJI[item_selected.rarity]} "
                f"[**{constants.RARITIES_LABELS[item_selected.rarity]}**] {item_selected.name}")

        characters_applicant = selected_chars[f"{user_that_reacted.name}#{user_that_reacted.discriminator}"].copy()
        del selected_chars[f"{user_that_reacted.name}#{user_that_reacted.discriminator}"]
        recipient_name = next(iter(selected_chars))
        recipient = utils.get(self.bot.get_all_members(), name=recipient_name.split("#")[0],
                              discriminator=recipient_name.split("#")[1])
        characters_recipient = selected_chars[recipient_name].copy()

        header_embed = self.generate_header_trade(user_that_reacted, recipient, characters_applicant,
                                                  characters_recipient)
        await origin_message.reference.resolved.edit(embed=header_embed)

    async def applicant_cancel_trade(self, origin_message: Message, user_that_reacted: User):
        author_name = origin_message.reference.resolved.embeds[0].author.name
        if author_name != f"{user_that_reacted.name}#{user_that_reacted.discriminator}":
            return
        await origin_message.reference.resolved.delete()
        await origin_message.delete()

    async def applicant_validate_trade(self, origin_message: Message, user_that_reacted: User):
        author_name = origin_message.reference.resolved.embeds[0].author.name
        user_that_reacted_name = f"{user_that_reacted.name}#{user_that_reacted.discriminator}"
        if author_name != user_that_reacted_name:
            return
        current_trade_author = origin_message.embeds[0].author.name

        if user_that_reacted_name != current_trade_author:
            await origin_message.reference.resolved.add_reaction(constants.RED_CROSS_EMOJI)
            await origin_message.reference.resolved.add_reaction(constants.CHECK_EMOJI)
            await origin_message.delete()
        else:
            fields = origin_message.reference.resolved.embeds[0].fields
            trade_users = []
            for field in fields:
                trade_users.append(field.name)
            trade_users.remove(user_that_reacted_name)
            author_embed = trade_users[0].split("#")
            current_user = utils.get(self.bot.get_all_members(), name=author_embed[0], discriminator=author_embed[1])
            query = (Character.select(Character)
                     .join(CharactersOwnership)
                     .where(CharactersOwnership.discord_user_id == current_user.id)
                     .order_by(Character.rarity.desc())).paginate(1, 10)
            content_embed = self.generate_content_trade(query, current_user)
            await origin_message.edit(embed=content_embed)

    async def applicant_cancel_confirm(self, origin_message: Message, user_that_reacted: User):
        if origin_message.reference.resolved.author.id != user_that_reacted.id:
            return
        await origin_message.delete()

    async def applicant_confirm(self, origin_message: Message, user_that_reacted: User):
        if origin_message.reference.resolved.author.id != user_that_reacted.id:
            return

        selected_chars = self.retrieve_selected_chars(origin_message.embeds[0])
        applicant_id = ""
        recipient_id = ""
        recipient_user = None
        applicant_chars = ""
        recipient_chars = ""
        confirmation_code = ""
        for user in selected_chars.keys():
            user_info = user.split("#")
            current_user = utils.get(self.bot.get_all_members(), name=user_info[0], discriminator=user_info[1])

            chars_id = ""
            for line in selected_chars[user]:
                chars_id += f"{line.split('•')[0].strip()}-"
            if chars_id:
                chars_id = chars_id[:-1]

            if current_user.id == user_that_reacted.id:
                applicant_id = current_user.id
                applicant_chars = chars_id
            else:
                recipient_id = current_user.id
                recipient_user = current_user
                recipient_chars = chars_id
            confirmation_code += chars_id
            confirmation_code += "|"
        confirmation_code = hashlib.sha256(confirmation_code.encode()).hexdigest()
        trade_model = Trade.create(applicant=applicant_id, recipient=recipient_id, applicant_cards=applicant_chars,
                                   recipient_cards=recipient_chars, confirmation_code=confirmation_code)
        trade_offer_embed = await self.generate_trade_offer(trade_model)
        trade_msg = await recipient_user.send(embed=trade_offer_embed)
        await origin_message.delete()
        await trade_msg.add_reaction(constants.RED_CROSS_EMOJI)
        await trade_msg.add_reaction(constants.CHECK_EMOJI)

    async def refuse_trade(self, origin_message: Message, user_that_reacted: User):
        selected_chars = self.retrieve_selected_chars(origin_message.embeds[0])
        user_name = f"{user_that_reacted.name}#{user_that_reacted.discriminator}"
        if user_name not in selected_chars:
            return
        trade_id = self.retrieve_trade_id(origin_message.embeds[0])
        trade_model = Trade.get(Trade.id == trade_id)
        if trade_model.state != 0:
            await user_that_reacted.send("The trade offer has already been completed, you cannot change the outcome.")
        else:
            trade_model.state = 1
            trade_model.save()
            applicant = await self.retrieve_member(trade_model.applicant)
            await applicant.send(f"Your trade offer with {user_that_reacted.name}#{user_that_reacted.discriminator} has"
                                 f" been refused.")

    async def accept_trade(self, origin_message: Message, user_that_reacted: User):
        selected_chars = self.retrieve_selected_chars(origin_message.embeds[0])
        user_name = f"{user_that_reacted.name}#{user_that_reacted.discriminator}"
        if user_name not in selected_chars:
            return
        trade_id = self.retrieve_trade_id(origin_message.embeds)
        trade_model = Trade.get(Trade.id == trade_id)
        if trade_model.state != 0:
            await user_that_reacted.send("The trade offer has already been completed, you cannot change the outcome.")
        else:
            applicant_cards = trade_model.applicant_cards.split("-")
            recipient_cards = trade_model.recipient_cards.split("-")

            if applicant_cards and len(applicant_cards) > 0:
                for card in applicant_cards:
                    if card:
                        ownership_model = CharactersOwnership.get(CharactersOwnership.id == int(card))
                        ownership_model.discord_user_id = trade_model.recipient
                        ownership_model.save()

            if recipient_cards and len(recipient_cards) > 0:
                for card in recipient_cards:
                    if card:
                        ownership_model = CharactersOwnership.get(CharactersOwnership.id == int(card))
                        ownership_model.discord_user_id = trade_model.applicant
                        ownership_model.save()

            trade_model.state = 2
            trade_model.save()
            await user_that_reacted.send("The trade is complete.")
            applicant = await self.retrieve_member(trade_model.applicant)
            await applicant.send(f"Your trade offer with {user_that_reacted.name}#{user_that_reacted.discriminator} has"
                                 f" been refused.")
