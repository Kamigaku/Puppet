from discord import User, Emoji
from discord.ext import commands
from discord.ext.commands import Context
from peewee import ModelSelect, fn

from discordClient.cogs.abstract import assignableCogs
from discordClient.helper import constants
from discordClient.model import Affiliation, CharacterAffiliation, CharactersOwnership, Character, Trade
from discordClient.views import ViewWithReactions, PageView123, Fields, Reaction


class TradeCogs(assignableCogs.AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "trade")

    ################################
    #       COMMAND COGS           #
    ################################

    @commands.command(name="trade")
    async def trade(self, ctx: Context, discord_user: User):
        # if discord_user.id == ctx.author.id:
        #     await ctx.author.send("You cannot trade with yourself.")

        fields = [Fields(title=f"{ctx.author.name}#{ctx.author.discriminator}",
                         data=TradeFieldData()),
                  Fields(title=f"{discord_user.name}#{discord_user.discriminator}",
                         data=TradeFieldData())]

        reaction_recap_menu = [Reaction(event_type=[constants.REACTION_ADD],
                                        emojis=constants.CHECK_EMOJI,
                                        callback=self.create_trade),
                               Reaction(event_type=[constants.REACTION_ADD],
                                        emojis=constants.RED_CROSS_EMOJI,
                                        callback=self.cancel_trade)]

        recap_menu = ViewWithReactions(puppet_bot=self.bot,
                                       menu_title="Trade recap",
                                       elements_to_display=[f"The section list the traded cards between "
                                                            f"**{ctx.author.mention}** and **{discord_user.mention}**"],
                                       author=ctx.author,
                                       bound_to=ctx.author,
                                       fields=fields,
                                       reactions=reaction_recap_menu,
                                       thumbnail=discord_user.avatar_url,
                                       delete_after=600)
        await recap_menu.display_menu(ctx)

        query, elements_to_display = self.generate_request(ctx.author.id)

        reaction_list_menu = [Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                       emojis=constants.ROTATE_EMOJI,
                                       callback=self.change_owner)]

        list_menu = PageView123(puppet_bot=self.bot,
                                menu_title="Summary of owned characters",
                                author=ctx.author,
                                elements_to_display=elements_to_display,
                                elements_per_page=10,
                                bound_to=ctx.author,
                                reactions=reaction_list_menu,
                                callback_number=self.update_trade_offer,
                                delete_after=600)

        trade_data = TradeData(request=query,
                               bounded_view=recap_menu,
                               origin=ctx.author,
                               destination=discord_user)
        list_menu.set_hidden_data(trade_data)
        recap_menu.set_hidden_data(list_menu)
        await list_menu.display_menu(ctx)

    ################################
    #       CALLBACKS              #
    ################################

    async def update_trade_offer(self, trade_menu: PageView123, user_that_reacted: User,
                                 emoji: Emoji = None):
        offset = constants.NUMBER_EMOJIS.index(emoji.name) - 1  # start at 1
        index = trade_menu.retrieve_index(offset)
        hidden_data = trade_menu.retrieve_hidden_data()
        if index < len(hidden_data.request):
            ownership = hidden_data.request[index]
            recap_menu_msg = hidden_data.bounded_view
            fields = recap_menu_msg.retrieve_fields()
            owner_list_name = f"{trade_menu.author.name}#{trade_menu.author.discriminator}"
            for field in fields:
                if field.title == owner_list_name:
                    field.data.update_data(ownership)
            await recap_menu_msg.update_menu()

    async def change_owner(self, list_menu: PageView123, user_that_reacted: User,
                           emoji: Emoji = None):
        trade_data = list_menu.retrieve_hidden_data()
        if trade_data.current_user == trade_data.origin:
            trade_data.current_user = trade_data.destination
        else:
            trade_data.current_user = trade_data.origin

        query, elements_to_display = self.generate_request(trade_data.current_user.id)

        trade_data.request = query
        list_menu.update_datas(author=trade_data.current_user,
                               elements_to_display=elements_to_display)
        await list_menu.update_menu()

    async def create_trade(self, list_menu: ViewWithReactions, user_that_reacted: User,
                           emoji: Emoji = None):
        await list_menu.retrieve_hidden_data().menu_msg.delete()
        await list_menu.menu_msg.delete()

        origin = list_menu.retrieve_hidden_data().retrieve_hidden_data().origin
        origin_id = origin.id
        destination = list_menu.retrieve_hidden_data().retrieve_hidden_data().destination
        destination_id = destination.id
        if type(list_menu.retrieve_field(0).data.data) is list:
            origin_cards = "-".join([str(o.id) for o in list_menu.retrieve_field(0).data.data])
        else:
            origin_cards = ""
        if type(list_menu.retrieve_field(1).data.data) is list:
            destination_cards = "-".join([str(o.id) for o in list_menu.retrieve_field(1).data.data])
        else:
            destination_cards = ""
        trade = Trade(applicant=origin_id,
                      recipient=destination_id,
                      applicant_cards=origin_cards,
                      recipient_cards=destination_cards)
        trade.save()

        reaction_recap_menu = [Reaction(event_type=[constants.REACTION_ADD],
                                        emojis=constants.CHECK_EMOJI,
                                        callback=self.accept_trade),
                               Reaction(event_type=[constants.REACTION_ADD],
                                        emojis=constants.RED_CROSS_EMOJI,
                                        callback=self.refuse_trade)]
        private_list_menu = ViewWithReactions(puppet_bot=self.bot,
                                              menu_title="Trade offer",
                                              elements_to_display=list_menu.elements,
                                              author=list_menu.author,
                                              fields=list_menu.fields,
                                              reactions=reaction_recap_menu,
                                              thumbnail=list_menu.thumbnail,
                                              msg_content=f"You have received a trade offer from "
                                                          f"{origin.name}#{origin.discriminator}")
        private_list_menu.set_hidden_data(trade)
        await private_list_menu.display_menu(destination)

    async def cancel_trade(self, list_menu: PageView123, user_that_reacted: User,
                           emoji: Emoji = None):
        await list_menu.retrieve_hidden_data().menu_msg.delete()
        await list_menu.menu_msg.delete()

    async def accept_trade(self, list_menu: ViewWithReactions, user_that_reacted: User,
                           emoji: Emoji = None):
        await list_menu.menu_msg.delete()
        trade = list_menu.retrieve_hidden_data()
        if trade.accept_trade():
            await user_that_reacted.send("The trade is complete.")
            applicant = await self.retrieve_member(trade.applicant)
            await applicant.send(f"Your trade offer with {user_that_reacted.name}#{user_that_reacted.discriminator} has"
                                 f" been accepted!")
        else:
            await user_that_reacted.send("The trade offer has already been completed, you cannot change the outcome.")

    async def refuse_trade(self, list_menu: ViewWithReactions, user_that_reacted: User,
                           emoji: Emoji = None):
        await list_menu.menu_msg.delete()
        trade = list_menu.retrieve_hidden_data()
        if trade.refuse_trade():
            applicant = await self.retrieve_member(trade.applicant)
            await applicant.send(f"Your trade offer with {user_that_reacted.name}#{user_that_reacted.discriminator} has"
                                 f" been refused.")
        else:
            await user_that_reacted.send("The trade offer has already been completed, you cannot change the outcome.")

    ################################
    #       UTILITIES              #
    ################################

    def generate_request(self, user_id):
        query = (CharactersOwnership.select(CharactersOwnership.id, CharactersOwnership.discord_user_id,
                                            Character.name, Character.category, Character.rarity, Character.id,
                                            fn.GROUP_CONCAT(Affiliation.name, ", ").alias("affiliations"))
                                    .join_from(CharactersOwnership, Character)
                                    .join_from(Character, CharacterAffiliation)
                                    .join_from(CharacterAffiliation, Affiliation)
                                    .where(CharactersOwnership.discord_user_id == user_id)
                                    .group_by(CharactersOwnership.id)
                                    .order_by(Character.rarity.desc(), Character.name.asc()))

        elements_to_display = []
        for ownership in query:
            character = ownership.character_id
            affiliation_text = ownership.affiliations
            character_field = f"{constants.RARITIES_EMOJI[character.rarity]} " \
                              f"**[{constants.RARITIES_LABELS[character.rarity]}] {character.name}**"
            character_field += f"\n{affiliation_text}\n"
            elements_to_display.append(character_field)
        return query, elements_to_display


class TradeData:

    def __init__(self, request: ModelSelect, bounded_view: ViewWithReactions, origin: User, destination: User):
        self.request = request
        self.bounded_view = bounded_view
        self.origin = origin
        self.destination = destination
        self.current_user = self.origin


class TradeFieldData:

    def __init__(self):
        self.data = []

    def __str__(self):
        if len(self.data) == 0:
            return "No character"
        else:
            character_list = ""
            for data in self.data:
                character_list += f"{constants.RARITIES_EMOJI[data.character_id.rarity]} ** " \
                                  f"[{constants.RARITIES_LABELS[data.character_id.rarity]}] " \
                                  f"{data.character_id.name} **\n"
            return character_list

    def update_data(self, data: CharactersOwnership):
        if data in self.data:
            self.data.remove(data)
        else:
            self.data.append(data)
