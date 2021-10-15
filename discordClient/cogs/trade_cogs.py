from discord import User
from peewee import ModelSelect, fn
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from discordClient.cogs.abstract import AssignableCogs
from discordClient.helper import constants
from discordClient.model import Affiliation, CharacterAffiliation, CharactersOwnership, Character, Trade
from discordClient.views import ViewWithReactions, Fields, Reaction, TradeRecapEmbedRender, \
    TradeNumbersListEmbedRender, PageViewSelectElement, ViewReactionsLine


class TradeCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "trade")

    ################################
    #       COMMAND COGS           #
    ################################

    @cog_ext.cog_slash(name="trade",
                       description="Start a trade with an user",
                       options=[
                           create_option(
                               name="user",
                               description="The user you will trade with",
                               option_type=SlashCommandOptionType.USER,
                               required=True,
                           )
                       ])
    async def trade(self, ctx: SlashContext, user: User):
        if user.id == ctx.author.id:
            await ctx.send("You cannot trade with yourself.")
            return

        # Recap menu - Display the characters selected
        fields = [Fields(title=f"{ctx.author.name}#{ctx.author.discriminator}",
                         data=TradeFieldData()),
                  Fields(title=f"{user.name}#{user.discriminator}",
                         data=TradeFieldData())]
        recap_render = TradeRecapEmbedRender(applicant=ctx.author,
                                             recipient=user)
        actions_line = ViewReactionsLine()
        actions_line.add_reaction(Reaction(button=constants.VALIDATE_BUTTON, callback=self.create_trade))
        actions_line.add_reaction(Reaction(button=constants.CANCEL_BUTTON, callback=self.cancel_trade))
        recap_menu = ViewWithReactions(puppet_bot=self.bot,
                                       elements_to_display=fields,
                                       render=recap_render,
                                       bound_to=ctx.author,
                                       lines=[actions_line],
                                       delete_after=600)
        await recap_menu.display_menu(ctx)

        query, elements_to_display = self.generate_request(ctx.author.id)

        # Trade menu - Selecting the characters to trade
        trade_list_render = TradeNumbersListEmbedRender(menu_title="Summary of owned characters",
                                                        current_owner=ctx.author)
        actions_line = ViewReactionsLine()
        actions_line.add_reaction(Reaction(button=constants.CHANGE_OWNER_BUTTON, callback=self.change_owner))
        list_menu = PageViewSelectElement(puppet_bot=self.bot,
                                          elements_to_display=query,
                                          render=trade_list_render,
                                          elements_per_page=10,
                                          bound_to=ctx.author,
                                          lines=[actions_line],
                                          callback_element_selection=self.update_trade_offer,
                                          delete_after=600)

        trade_data = TradeData(request=query,
                               bounded_view=recap_menu,
                               origin=ctx.author,
                               destination=user)
        list_menu.set_hidden_data(trade_data)
        recap_menu.set_hidden_data(list_menu)
        await list_menu.display_menu(ctx)

    ################################
    #       CALLBACKS              #
    ################################

    @staticmethod
    async def update_trade_offer(context, menu, selected_index, selected_element):
        await context.defer(ignore=True)
        hidden_data = menu.get_hidden_data()
        recap_menu_msg = hidden_data.bounded_view
        fields = recap_menu_msg.elements
        owner_list_name = f"{menu.render.current_owner.name}#{menu.render.current_owner.discriminator}"
        for field in fields:
            if field.title == owner_list_name:
                field.data.update_data(selected_element)
        await recap_menu_msg.update_menu(message=recap_menu_msg.menu_msg)
        # p-ê ici refresh le menu courant aussi ? sinon la selection ne disparait pas

    async def change_owner(self, **t):
        menu = t["menu"]
        context = t["context"]
        trade_data = menu.get_hidden_data()
        if trade_data.current_user == trade_data.origin:
            trade_data.current_user = trade_data.destination
        else:
            trade_data.current_user = trade_data.origin

        query, elements_to_display = self.generate_request(trade_data.current_user.id)
        trade_data.request = query

        trade_list_render = TradeNumbersListEmbedRender(menu_title="Summary of owned characters",
                                                        current_owner=trade_data.current_user)
        menu.update_datas(elements_to_display=query,
                          render=trade_list_render)
        await menu.update_menu(context=context)

    async def create_trade(self, **t):
        menu = t["menu"]
        await menu.get_hidden_data().menu_msg.delete()
        await menu.remove_components(message=menu.menu_msg)

        origin = menu.get_hidden_data().get_hidden_data().origin
        origin_id = origin.id
        destination = menu.get_hidden_data().get_hidden_data().destination
        destination_id = destination.id
        if type(menu.elements[0].data.data) is list:
            origin_cards = "-".join([str(o.id) for o in menu.elements[0].data.data])
        else:
            origin_cards = ""
        if type(menu.elements[1].data.data) is list:
            destination_cards = "-".join([str(o.id) for o in menu.elements[1].data.data])
        else:
            destination_cards = ""
        trade = Trade(applicant=origin_id,
                      recipient=destination_id,
                      applicant_cards=origin_cards,
                      recipient_cards=destination_cards)
        trade.save()

        private_list_render = TradeRecapEmbedRender(msg_content=f"You have received a trade offer from "
                                                                f"{origin.name}#{origin.discriminator}.",
                                                    menu_title="Trade offer",
                                                    applicant=origin,
                                                    recipient=destination)
        actions_line = ViewReactionsLine()
        actions_line.add_reaction(Reaction(button=constants.VALIDATE_BUTTON, callback=self.accept_trade))
        actions_line.add_reaction(Reaction(button=constants.CANCEL_BUTTON, callback=self.refuse_trade))
        private_list_menu = ViewWithReactions(puppet_bot=self.bot,
                                              elements_to_display=menu.elements,
                                              render=private_list_render,
                                              lines=[actions_line],
                                              delete_after=600)

        private_list_menu.set_hidden_data(trade)
        await private_list_menu.display_menu(destination)
        await origin.send(f"Your trade offer has been sent to {destination.name}#{destination.discriminator}.")

    @staticmethod
    async def cancel_trade(**t):
        context = t["context"]
        await context.defer(ignore=True)
        menu = t["menu"]
        await menu.get_hidden_data().menu_msg.delete()
        await menu.menu_msg.delete()

    async def accept_trade(self, **t):
        context = t["context"]
        menu = t["menu"]
        user_that_interact = t["user_that_interact"]
        trade = menu.get_hidden_data()
        if trade.accept_trade():
            applicant = await self.retrieve_member(trade.applicant)
            await user_that_interact.send(f"You have accepted the trade offer from "
                                          f"{applicant.name}#{applicant.discriminator}")
            await applicant.send(f"Your trade offer with {user_that_interact.name}#{user_that_interact.discriminator} "
                                 f"has been accepted!")
        else:
            await user_that_interact.send("The trade offer has already been completed, you cannot change the outcome.")
        await menu.remove_components(context=context)

    async def refuse_trade(self, **t):
        context = t["context"]
        menu = t["menu"]
        user_that_interact = t["user_that_interact"]
        trade = menu.get_hidden_data()
        if trade.refuse_trade():
            applicant = await self.retrieve_member(trade.applicant)
            await applicant.send(f"Your trade offer with {user_that_interact.name}#{user_that_interact.discriminator} "
                                 f"has been refused.")
        else:
            await user_that_interact.send("The trade offer has already been completed, you cannot change the outcome.")
        await menu.remove_components(context=context)

    ################################
    #       UTILITIES              #
    ################################

    @staticmethod
    def generate_request(user_id):
        query = (CharactersOwnership.select(CharactersOwnership.id, CharactersOwnership.discord_user_id,
                                            Character.name, Character.category, Character.rarity, Character.id,
                                            fn.GROUP_CONCAT(Affiliation.name, ", ").alias("affiliations"))
                                    .join_from(CharactersOwnership, Character)
                                    .join_from(Character, CharacterAffiliation)
                                    .join_from(CharacterAffiliation, Affiliation)
                                    .where((CharactersOwnership.discord_user_id == user_id) &
                                           (CharactersOwnership.is_sold == False) &
                                           (CharactersOwnership.is_locked == False))
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
