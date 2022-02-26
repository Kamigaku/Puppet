import typing

import math
from typing import Any, List

import discord
from discord.ui import Button, Select, Item, View

from discord import User, Message, ButtonStyle, SelectOption, ActionRow, Interaction, Client
from discord.abc import Messageable
from discord.ext.commands import InteractionContext

from discordClient.helper import constants
from discordClient.views.renders import EmbedRender


class Reaction:

    def __init__(self, button: Item, callback: typing.Any):
        self.button = button
        self.callback = callback


class ViewWithHiddenData(View):

    def __init__(self,
                 puppet_bot,
                 elements_to_display: Any,
                 render: EmbedRender | None,
                 bound_to: User | None = None,
                 delete_after: int | None = None,
                 hidden_data: Any | None = None):
        super().__init__(timeout=delete_after)
        self.puppet_bot = puppet_bot
        self.elements = elements_to_display
        self.render = render
        self.bound_to = bound_to
        self.menu_msg: discord.Message = None
        self.hidden_data = hidden_data

    def dispose(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_reaction_listener(self.menu_msg.id)

    def set_hidden_data(self, hidden_data: Any):
        self.hidden_data = hidden_data

    def get_hidden_data(self) -> Any:
        return self.hidden_data

    async def display_view(self, messageable: Messageable, send_has_reply: bool = True) -> Message:
        if send_has_reply:
            self.menu_msg = await messageable.send(content=self.render.generate_content(),
                                                   embed=self.render.generate_render(data=self.elements),
                                                   view=self)
        else:
            channel = await messageable._get_channel()
            self.menu_msg = await channel.send(content=self.render.generate_content(),
                                               embed=self.render.generate_render(data=self.elements),
                                               view=self)

        # je sais plus à quoi ça sert
        # for line in self.lines:
        #     for reaction in line.reactions:
        #         self.puppet_bot.append_reaction_listener(ReactionListener(callback=self.reaction_callback,
        #                                                                   message=self.menu_msg,
        #                                                                   interaction_id=reaction.button["custom_id"],
        #                                                                   bound_to=self.bound_to))
        #
        # if self.menu_msg is not None:
        #     self.puppet_bot.append_delete_listener(DeleteListener(message=self.menu_msg,
        #                                                           disposable_object=self))
        return self.menu_msg

    async def update_view(self):
        if self.menu_msg is not None:
            await self.menu_msg.edit(content=self.render.generate_content(),
                                     embed=self.render.generate_render(data=self.elements),
                                     view=self)

    def update_datas(self, elements_to_display: List = None, render: EmbedRender = None):
        if elements_to_display is not None:
            self.elements = elements_to_display
        if render is not None:
            self.render = render

    # async def reaction_callback(self, **d):
    #     for line in self.lines:
    #         for reaction in line.reactions:
    #             if reaction.button.custom_id == d["context"].custom_id:
    #                 await reaction.callback(menu=self,
    #                                         user_that_interact=d["user_that_interact"],
    #                                         context=d["context"])
    #
    # def create_line(self) -> ViewReactionsLine:
    #     new_line = ViewReactionsLine()
    #     self.lines.append(new_line)
    #     return new_line
    #
    # def generate_actions_row(self) -> List:
    #     actions_row = []
    #     for line in self.lines:
    #         actions_row.append(line.create_action_row())
    #     return actions_row
    #
    # def retrieve_button(self, custom_id: str):
    #     for line in self.lines:
    #         reaction = line.retrieve_button(custom_id=custom_id)
    #         if reaction is not None:
    #             return reaction
    #     return None

    # async def remove_components(self, interaction: Interaction):
    #     if self.menu_msg is not None:
    #         self.lines.clear()
    #         self.puppet_bot.execute_delete_listener(self.menu_msg.id)
    #         await self.update_menu(interaction=interaction)


class PageView(ViewWithHiddenData):

    def __init__(self, puppet_bot,
                 elements_to_display: typing.List,
                 render: EmbedRender,
                 hidden_data: typing.Any=  None,
                 bound_to: User | None = None,
                 delete_after: int | None = None,
                 callback_prev: typing.Callable = None,
                 callback_next: typing.Callable = None,
                 callback_select: typing.Callable = None,
                 elements_per_page: int = 1):
        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         hidden_data=hidden_data,
                         delete_after=delete_after)

        # Prepare the GUI
        disabled = len(elements_to_display) < elements_per_page

        # Previous button
        previous_button = Button(style=ButtonStyle.blurple,
                                 label="Previous page",
                                 emoji=constants.LEFT_ARROW_EMOJI,
                                 disabled=disabled,
                                 row=0)
        previous_button.callback = self.previous_page

        # Next button
        next_button = Button(style=ButtonStyle.blurple,
                             label="Next page",
                             emoji=constants.RIGHT_ARROW_EMOJI,
                             disabled=disabled,
                             row=0)
        next_button.callback = self.next_page

        # Page select
        page_select_options: list[SelectOption] = []
        for i in range(1, min(math.ceil(len(elements_to_display) / elements_per_page) + 1, 26)):
            page_select_options.append(SelectOption(label=f"Page #{i}",
                                                    value=f"{i - 1}"))

        disabled = len(page_select_options) < 2
        self.page_select = Select(options=page_select_options,
                                  placeholder="Select the page you want to go to",
                                  disabled=disabled,
                                  row=1)
        self.page_select.callback = self.select_page

        # Assemble the GUI
        self.add_item(previous_button)
        self.add_item(next_button)
        self.add_item(self.page_select)  # TODO: pas trop fan du fait de le mettre en "self.", à étudier

        self.elements_per_page = elements_per_page
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.callback_select = callback_select
        self.page = 0

    async def display_view(self, messageable: Messageable, send_has_reply: bool = True) -> Message:
        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.page * self.elements_per_page:
                                                (self.page + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.page]

        content = self.render.generate_content()
        embed = self.render.generate_render(data=elements_to_display,
                                            page=self.page,
                                            starting_index=(self.page * self.elements_per_page))

        if send_has_reply:
            self.menu_msg = await messageable.send(content=content,
                                                   embed=embed,
                                                   view=self)
        else:
            channel = await messageable._get_channel()
            self.menu_msg = await channel.send(content=content,
                                               embed=embed,
                                               view=self)

        return self.menu_msg

    async def update_view(self):
        if len(self.elements) <= 0:
            await self.menu_msg.edit(content="No element for this view.",
                                     embed=None)
            return

        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.page * self.elements_per_page:
                                                (self.page + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.page]

        embed = self.render.generate_render(data=elements_to_display,
                                            page=self.page,
                                            starting_index=(self.page * self.elements_per_page))

        # Refresh the select field
        page_select_options: typing.List[SelectOption] = []
        max_number_pages = math.ceil(len(self.elements) / self.elements_per_page) + 1
        starting_value = max(self.page - 12, 0)
        for i in range(1, 26):
            if i + starting_value < max_number_pages:
                page_select_options.append(SelectOption(label=f"Page #{i + starting_value}",
                                                        value=f"{i + starting_value - 1}"))
            else:
                break
        if len(page_select_options) == 0:
            self.page_select.disabled = True
        else:
            self.page_select.options = page_select_options
        if self.menu_msg is not None:
            await self.menu_msg.edit(content=self.render.generate_content(),
                                     embed=self.render.generate_render(data=elements_to_display,
                                                                       page=self.page,
                                                                       starting_index=(self.page * self.elements_per_page)),
                                     view=self)

    def update_datas(self, elements_to_display: List = None, render: EmbedRender = None,
                     elements_per_page: int = None):
        super().update_datas(elements_to_display=elements_to_display,
                             render=render)
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page
        self.page = 0

    async def go_to_page(self, page: int):
        self.page = page
        await self.update_view()

    async def next_page(self, interaction: Interaction):
        self.page += 1
        if self.page * self.elements_per_page >= len(self.elements):
            self.page -= 1
            await interaction.response.defer(ephemeral=True)
            return
        await self.update_view()
        if self.callback_next is not None:
            await self.callback_next(view=self,
                                     interaction=interaction)

    async def previous_page(self, interaction: Interaction):
        self.page -= 1
        if self.page < 0:
            self.page = 0
            await interaction.response.defer(ephemeral=True)
            return
        await self.update_view()
        if self.callback_prev is not None:
            await self.callback_prev(view=self,
                                     interaction=interaction)

    async def select_page(self, interaction: Interaction):
        selected_option = int(interaction.data['values'][0])
        if selected_option != self.page:
            self.page = selected_option
            await self.update_view()
            if self.callback_select is not None:
                await self.callback_select(view=self,
                                           interaction=interaction)
        else:
            await interaction.response.defer(ephemeral=True)

    def retrieve_element(self, index):
        if index < len(self.elements):
            return self.elements[index]
        return None

    def retrieve_element_by_offset(self, offset: int = 0):
        return self.retrieve_element(self.retrieve_index(offset))

    def retrieve_index(self, offset: int = 0) -> int:
        return self.page * self.elements_per_page + offset


class PageViewSelectElement(PageView):

    def __init__(self, puppet_bot, elements_to_display: List, render: EmbedRender,
                 bound_to: User = None,
                 delete_after: int = None,
                 hidden_data: typing.Any = None,
                 callback_prev: typing.Callable = None,
                 callback_next: typing.Callable = None,
                 elements_per_page: int = 1,
                 callback_element_selection: typing.Callable = None):
        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         hidden_data=hidden_data,
                         delete_after=delete_after,
                         callback_next=callback_next,
                         callback_prev=callback_prev,
                         elements_per_page=elements_per_page)


        # Create the elements selection
        elements_select_options: typing.List[SelectOption] = []
        for i in range(0, elements_per_page):
            if i < len(elements_to_display):
                elements_select_options.append(SelectOption(label=f"{elements_to_display[i]}",
                                                            value=f"{i}"))

        disabled = len(elements_select_options) == 0  # if we don't have elements we disabled the selection
        if disabled:
            elements_select_options.append(SelectOption(label="Invalid element",
                                                        value=str(-1)))
        self.element_select = Select(options=elements_select_options,
                                     placeholder="Select an element",
                                     disabled=disabled,
                                     row=2)
        self.element_select.callback = self.element_selected
        self.add_item(self.element_select)
        self.callback_element_selection = callback_element_selection

    async def update_view(self):
        elements_select_options: typing.List[SelectOption] = []
        for i in range(0, self.elements_per_page):
            index = (self.page * self.elements_per_page) + i
            if index < len(self.elements):
                elements_select_options.append(
                    SelectOption(label=f"{self.elements[index]}",
                                 value=f"{index}"))
            else:
                break
        if len(elements_select_options) > 0:  # if we don't have elements or only one, we don't display it
            self.element_select.options = elements_select_options
        else:
            self.element_select.disabled = True
        await super().update_view()

    async def element_selected(self, interaction: Interaction):
        if self.callback_element_selection is not None:
            selected_option = int(interaction.data['values'][0])
            selected_element = self.retrieve_element(selected_option)
            if selected_element is not None:
                await self.callback_element_selection(interaction=interaction,
                                                      menu=self,
                                                      selected_index=selected_option,
                                                      selected_element=selected_element)

