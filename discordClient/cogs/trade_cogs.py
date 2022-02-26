import discord.ui
from discord import User, Interaction
from peewee import ModelSelect, fn

from discord.ext.commands import slash_command, InteractionContext, ApplicationCommandField
from discordClient.cogs.abstract import AssignableCogs, BaseCogs
from discordClient.helper import constants
from discordClient.model import Affiliation, CharacterAffiliation, CharactersOwnership, Character, Trade
from discordClient.views import ViewWithReactions, Fields, Reaction, TradeRecapEmbedRender, \
    TradeCharactersListEmbedRender, ViewReactionsLine, List, ValidateTradeButton, CancelTradeButton, ChangeOwnerButton
from discordClient.views.view import ViewWithHiddenData, PageViewSelectElement


class TradeCogs(AssignableCogs):

    def __init__(self, bot):
        super().__init__(bot, "trade")

    ################################
    #       COMMAND COGS           #
    ################################

    @slash_command(description="Start a trade with an user",
                   is_global=True)
    @BaseCogs.disabled
    @AssignableCogs.restricted
    async def trade(self,
                    interaction: InteractionContext,
                    user: User = ApplicationCommandField(description="The user you will trade with",
                                                         required=True)):
        # if user.id == interaction.author.id:
        #     await interaction.send(content="You cannot trade with yourself.",
        #                            ephemeral=True)
        #     return

        # Recap menu - Display the characters selected
        fields = [Fields(title=f"{interaction.author.name}#{interaction.author.discriminator}",
                         data=TradeFieldData()),
                  Fields(title=f"{user.name}#{user.discriminator}",
                         data=TradeFieldData())]
        recap_render = TradeRecapEmbedRender(applicant=interaction.author,
                                             recipient=user)

        recap_menu = ViewWithHiddenData(puppet_bot=self.bot,
                                        elements_to_display=fields,
                                        render=recap_render,
                                        bound_to=interaction.author,
                                        delete_after=600)
        recap_menu.add_items([ValidateTradeButton(row=2,
                                                  callback_method=self.create_trade),
                              CancelTradeButton(row=2,
                                                callback_method=self.cancel_trade)])
        await recap_menu.display_view(messageable=interaction)

        query, elements_to_display = self.generate_request(interaction.author.id)

        # Trade menu - Selecting the characters to trade
        trade_list_render = TradeCharactersListEmbedRender(menu_title="Summary of owned characters",
                                                           current_owner=interaction.author)

        list_menu = PageViewSelectElement(puppet_bot=self.bot,
                                          elements_to_display=query,
                                          render=trade_list_render,
                                          elements_per_page=10,
                                          bound_to=interaction.author,
                                          callback_element_selection=self.update_trade_offer,
                                          delete_after=600)
        list_menu.add_item(ChangeOwnerButton(row=3))

        trade_data = TradeData(request=query,
                               bounded_view=recap_menu,
                               origin=interaction.author,
                               destination=user)
        list_menu.set_hidden_data(trade_data)
        recap_menu.set_hidden_data(list_menu)
        await list_menu.display_view(messageable=interaction,
                                     send_has_reply=False)

    ################################
    #       CALLBACKS              #
    ################################

    @staticmethod
    async def update_trade_offer(interaction: Interaction,
                                 menu: PageViewSelectElement,
                                 selected_index: int,
                                 selected_element: Character):
        await interaction.response.defer(ephemeral=True)
        hidden_data: TradeData = menu.get_hidden_data()
        recap_menu_msg: ViewWithHiddenData = hidden_data.bounded_view
        fields = recap_menu_msg.elements
        owner_list_name = f"{menu.render.current_owner.name}#{menu.render.current_owner.discriminator}"
        for field in fields:
            if field.title == owner_list_name:
                field.data.update_data(selected_element)
        #await recap_menu_msg.update_menu(message=recap_menu_msg.menu_msg)
        await recap_menu_msg.menu_msg.edit(embed=hidden_data.bounded_view.render.generate_render(
            data=hidden_data.bounded_view.elements))  # TODO: mon dieu c'est horrible
        # p-ê ici refresh le menu courant aussi ? sinon la selection ne disparait pas

    async def create_trade(self,
                           button: discord.ui.Button,
                           interaction: Interaction):
        view = button.view
        await view.get_hidden_data().menu_msg.delete()
        view.clear_items()
        await view.update_view()

        origin = view.get_hidden_data().get_hidden_data().origin
        origin_id = origin.id
        destination: User = view.get_hidden_data().get_hidden_data().destination
        destination_id = destination.id
        if type(view.elements[0].data.data) is list:
            origin_cards = "-".join([str(o.id) for o in view.elements[0].data.data])
        else:
            origin_cards = ""
        if type(view.elements[1].data.data) is list:
            destination_cards = "-".join([str(o.id) for o in view.elements[1].data.data])
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
        # actions_line = ViewReactionsLine()
        # actions_line.add_reaction(Reaction(button=constants.VALIDATE_BUTTON, callback=self.accept_trade))
        # actions_line.add_reaction(Reaction(button=constants.CANCEL_BUTTON, callback=self.refuse_trade))
        private_list_menu = ViewWithHiddenData(puppet_bot=self.bot,
                                               elements_to_display=view.elements,
                                               render=private_list_render,
                                               delete_after=600)
        private_list_menu.add_items([ValidateTradeButton(row=0,
                                                         callback_method=self.accept_trade),
                                     CancelTradeButton(row=0,
                                                       callback_method=self.refuse_trade)])
        private_list_menu.set_hidden_data(trade)
        await private_list_menu.display_view(messageable=destination)
        await origin.send(f"Your trade offer has been sent to {destination.name}#{destination.discriminator}.")

    async def accept_trade(self,
                           button: discord.ui.Button,
                           interaction: Interaction):
        trade = button.view.get_hidden_data()
        if trade.accept_trade():
            applicant = await self.retrieve_member(trade.applicant)
            await interaction.user.send(f"You have accepted the trade offer from "
                                        f"{applicant.name}#{applicant.discriminator}")
            await applicant.send(content=f"Your trade offer with "
                                         f"{interaction.user.name}#{interaction.user.discriminator} has been accepted!")
        else:
            await interaction.user.send(content="The trade offer has already been completed, you cannot "
                                                "change the outcome.")
        button.view.clear_items()
        await button.view.update_view()

    async def refuse_trade(self,
                           button: discord.ui.Button,
                           interaction: Interaction):
        trade = button.view.get_hidden_data()
        if trade.refuse_trade():
            applicant = await self.retrieve_member(trade.applicant)
            await interaction.user.send(f"You have refused the trade offer from "
                                        f"{applicant.name}#{applicant.discriminator}")
            await applicant.send(f"Your trade offer with {interaction.user.name}#{interaction.user.discriminator} "
                                 f"has been refused.")
        else:
            await interaction.user.send("The trade offer has already been completed, you cannot change the outcome.")
        button.view.clear_items()
        await button.view.update_view()

    @staticmethod
    async def cancel_trade(button: discord.ui.Button,
                           interaction: Interaction):
        await interaction.response.defer(ignore=True)
        await button.view.get_hidden_data().menu_msg.delete()
        await button.view.menu_msg.delete()
    ################################
    #       UTILITIES              #
    ################################

    # TODO: Dupliqué dans le code des boutons
    @staticmethod
    def generate_request(user_id, rarity: List[int] = None, affiliation: str = None):
        query = (CharactersOwnership.select(CharactersOwnership.id, CharactersOwnership.discord_user_id,
                                            Character.name, Character.category, Character.rarity, Character.id,
                                            fn.GROUP_CONCAT(Affiliation.name, ", ").alias("affiliations"))
                 .join_from(CharactersOwnership, Character)
                 .join_from(Character, CharacterAffiliation)
                 .join_from(CharacterAffiliation, Affiliation))

        if rarity is not None:
            query = query.where(Character.rarity << rarity)
        if affiliation is not None:
            query = (query.where(Affiliation.name == affiliation))

        query = (query.where((CharactersOwnership.discord_user_id == user_id) &
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

    def __init__(self, request: ModelSelect, bounded_view: ViewWithHiddenData, origin: User, destination: User):
        self.request: ModelSelect = request
        self.bounded_view: ViewWithHiddenData = bounded_view
        self.origin: User = origin
        self.destination: User = destination
        self.current_user: User = self.origin


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


def setup(bot):
    bot.add_cog(TradeCogs(bot))
