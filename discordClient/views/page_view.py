from typing import Any, List
import math

from discord import User, Message
from discord_slash import ComponentMessage
from discord_slash.context import InteractionContext, ComponentContext
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select, create_select_option
from discord_slash.model import ButtonStyle

from discordClient.helper import constants
from discordClient.helper import Disposable, ReactionListener, DeleteListener
from discordClient.views.renders import EmbedRender, ListEmbedRender


class Reaction:

    def __init__(self, button, callback):
        self.button = button
        self.callback = callback


class ViewReactionsLine:

    def __init__(self):
        self.reactions = []

    def add_reaction(self, reaction: Reaction):
        self.reactions.append(reaction)

    def create_action_row(self):
        buttons = []
        for reaction in self.reactions:
            buttons.append(reaction.button)
        return create_actionrow(*buttons)

    def retrieve_button(self, custom_id: str):
        for reaction in self.reactions:
            if reaction.button["custom_id"] == custom_id:
                return reaction
        return None


class ViewWithReactions(Disposable):

    def __init__(self, puppet_bot, elements_to_display: Any, render: EmbedRender,
                 lines: List[ViewReactionsLine] = [],
                 bound_to: User = None, delete_after: int = None):
        self.puppet_bot = puppet_bot
        self.elements = elements_to_display
        self.render = render
        self.bound_to = bound_to
        self.delete_after = delete_after
        self.menu_msg = None
        self.hidden_data = None
        self.lines = lines

    def dispose(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_reaction_listener(self.menu_msg.id)

    def set_hidden_data(self, hidden_data: Any):
        self.hidden_data = hidden_data

    def get_hidden_data(self) -> Any:
        return self.hidden_data

    async def display_menu(self, context: InteractionContext) -> Message:
        actions_row = []
        for line in self.lines:
            actions_row.append(line.create_action_row())
        self.menu_msg = await context.send(content=self.render.generate_content(),
                                           embed=self.render.generate_render(self.elements),
                                           components=actions_row)

        for line in self.lines:
            for reaction in line.reactions:
                self.puppet_bot.append_reaction_listener(ReactionListener(callback=self.reaction_callback,
                                                                          message=self.menu_msg,
                                                                          interaction_id=reaction.button["custom_id"],
                                                                          bound_to=self.bound_to))

        if self.menu_msg is not None:
            self.puppet_bot.append_delete_listener(DeleteListener(message=self.menu_msg,
                                                                  disposable_object=self))
        return self.menu_msg

    async def update_menu(self, context: ComponentContext = None, message: ComponentMessage = None):
        if context is None and message is None:
            return
        actions_row = []
        for line in self.lines:
            actions_row.append(line.create_action_row())
        if context is not None:
            await context.edit_origin(content=self.render.generate_content(),
                                      embed=self.render.generate_render(self.elements),
                                      components=actions_row)
        else:
            await message.edit(content=self.render.generate_content(),
                               embed=self.render.generate_render(self.elements),
                               components=actions_row)

    def update_datas(self, elements_to_display: List = None, render: EmbedRender = None):
        if elements_to_display is not None:
            self.elements = elements_to_display
        if render is not None:
            self.render = render

    async def reaction_callback(self, **d):
        for line in self.lines:
            for reaction in line.reactions:
                if reaction.button["custom_id"] == d["context"].custom_id:
                    await reaction.callback(menu=self,
                                            user_that_interact=d["user_that_interact"],
                                            context=d["context"])

    def create_line(self) -> ViewReactionsLine:
        new_line = ViewReactionsLine()
        self.lines.append(new_line)
        return new_line

    def generate_actions_row(self) -> List:
        actions_row = []
        for line in self.lines:
            actions_row.append(line.create_action_row())
        return actions_row

    def retrieve_button(self, custom_id: str):
        for line in self.lines:
            reaction = line.retrieve_button(custom_id=custom_id)
            if reaction is not None:
                return reaction
        return None

    async def remove_components(self, context: ComponentContext = None, message: ComponentMessage = None):
        if self.menu_msg is not None:
            self.lines.clear()
            self.puppet_bot.execute_delete_listener(self.menu_msg.id)
            await self.update_menu(context=context, message=message)


class PageView(ViewWithReactions):

    def __init__(self, puppet_bot, elements_to_display: List, render: ListEmbedRender,
                 bound_to: User = None, lines: List[ViewReactionsLine] = [],
                 delete_after: int = None,
                 callback_prev=None, callback_next=None, callback_select=None,
                 elements_per_page: int = 1):
        if lines is not None:
            lines = lines.copy()

        disabled = len(elements_to_display) < elements_per_page
        # First line - Next and previous page buttons
        next_button = create_button(
            style=ButtonStyle.blue,
            label="Next page",
            custom_id="next_page",
            emoji=constants.RIGHT_ARROW_EMOJI,
            disabled=disabled
        )
        previous_button = create_button(
            style=ButtonStyle.blue,
            label="Previous page",
            custom_id="previous_page",
            emoji=constants.LEFT_ARROW_EMOJI,
            disabled=disabled
        )

        buttons_line = ViewReactionsLine()
        buttons_line.add_reaction(Reaction(button=previous_button, callback=self.previous_page))
        buttons_line.add_reaction(Reaction(button=next_button, callback=self.next_page))
        lines.insert(0, buttons_line)

        # Add at the end - Page select
        page_select_options = []
        for i in range(1, min(math.ceil(len(elements_to_display) / elements_per_page) + 1, 26)):
            page_select_options.append(create_select_option(f"Page #{i}", value=f"{i - 1}"))

        disabled = len(page_select_options) < 2
        page_select = create_select(options=page_select_options, placeholder="Select the page you want to go to",
                                    custom_id="page_select", disabled=disabled)
        page_select_line = ViewReactionsLine()
        page_select_line.add_reaction(Reaction(button=page_select, callback=self.select_page))
        # Add select to GUI
        lines.append(page_select_line)

        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         delete_after=delete_after,
                         lines=lines)

        self.elements_per_page = elements_per_page
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.callback_select = callback_select
        self.offset = 0

    async def display_menu(self, context: InteractionContext) -> Message:
        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.offset * self.elements_per_page:
                                                (self.offset + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.offset]

        content = self.render.generate_content()
        embed = self.render.generate_render(elements_to_display, self.offset, self.offset * self.elements_per_page)
        actions_row = self.generate_actions_row()

        self.menu_msg = await context.send(content=content, embed=embed, components=actions_row)

        self.puppet_bot.append_delete_listener(DeleteListener(message=self.menu_msg,
                                                              disposable_object=self))
        for line in self.lines:
            for reaction in line.reactions:
                self.puppet_bot.append_reaction_listener(ReactionListener(callback=self.reaction_callback,
                                                                          message=self.menu_msg,
                                                                          interaction_id=reaction.button["custom_id"],
                                                                          bound_to=self.bound_to))

        return self.menu_msg

    async def update_menu(self, context: ComponentContext = None, message: ComponentMessage = None):
        if context is None and message is None:
            return

        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.offset * self.elements_per_page:
                                                (self.offset + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.offset]

        for line in self.lines:
            reaction = line.retrieve_button("page_select")
            if reaction is not None:
                page_select_options = []
                max_number_pages = math.ceil(len(self.elements) / self.elements_per_page) + 1
                starting_value = max(self.offset - 12, 0)
                for i in range(1, 26):
                    if i + starting_value < max_number_pages:
                        page_select_options.append(create_select_option(f"Page #{i + starting_value}",
                                                                        value=f"{i + starting_value - 1}"))
                    else:
                        break
                if len(page_select_options) == 0:
                    reaction.button["disabled"] = True
                else:
                    select_button = create_select(options=page_select_options,
                                                  placeholder="Select the page you want to go to",
                                                  custom_id="page_select")
                    reaction.button = select_button

                break

        # Edit the UI
        content = self.render.generate_content()
        embed = self.render.generate_render(elements_to_display, self.offset, self.offset * self.elements_per_page)

        components = self.generate_actions_row()

        if context is not None:
            await context.edit_origin(content=content, embed=embed, components=components)
        else:
            await message.edit(content=content, embed=embed, components=components)

    def update_datas(self, elements_to_display: List = None, render: EmbedRender = None,
                     elements_per_page: int = None):
        super().update_datas(elements_to_display=elements_to_display,
                             render=render)
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page
        self.offset = 0

    async def next_page(self, **t):
        self.offset += 1
        if self.offset * self.elements_per_page >= len(self.elements):
            self.offset -= 1
            await t["context"].defer(ignore=True)
            return
        await self.update_menu(t["context"])
        if self.callback_next is not None:
            self.callback_next(menu=t["menu"],
                               user_that_interact=t["user_that_interact"])

    async def previous_page(self, **t):
        self.offset -= 1
        if self.offset < 0:
            self.offset = 0
            await t["context"].defer(ignore=True)
            return
        await self.update_menu(t["context"])
        if self.callback_prev is not None:
            self.callback_prev(menu=t["menu"],
                               user_that_interact=t["user_that_interact"])

    async def select_page(self, **t):
        selected_option = int(t["context"].selected_options[0])
        if selected_option != self.offset:
            self.offset = selected_option
            await self.update_menu(t["context"])
            if self.callback_prev is not None:
                self.callback_select(menu=t["menu"],
                                     user_that_interact=t["user_that_interact"])
        else:
            await t["context"].defer(ignore=True)

    def retrieve_element(self, index):
        if index < len(self.elements):
            return self.elements[index]
        return None

    def retrieve_element_by_offset(self, offset: int):
        return self.retrieve_element(self.retrieve_index(offset))

    def retrieve_index(self, offset: int = 0) -> int:
        return self.offset * self.elements_per_page + offset


class PageViewSelectElement(PageView):

    def __init__(self, puppet_bot, elements_to_display: List, render: ListEmbedRender,
                 bound_to: User = None, lines: List[ViewReactionsLine] = [],
                 delete_after: int = None,
                 callback_prev=None, callback_next=None, callback_select=None,
                 elements_per_page: int = 1,
                 callback_element_selection=None):

        if lines is not None:
            lines = lines.copy()

        # Create the elements selection
        elements_select_options = []
        for i in range(0, elements_per_page):
            if i < len(elements_to_display):
                elements_select_options.append(create_select_option(f"{elements_to_display[i]}", value=f"{i}"))

        disabled = len(elements_select_options) == 0  # if we don't have elements we disabled the selection
        if disabled:
            elements_select_options.append(create_select_option("Invalid element", value=str(-1)))
        element_select = create_select(options=elements_select_options,
                                       placeholder="Select an element",
                                       custom_id="element_select",
                                       disabled=disabled)
        page_select_line = ViewReactionsLine()
        page_select_line.add_reaction(Reaction(button=element_select, callback=self.element_selected))
        # Add select to GUI
        lines.append(page_select_line)

        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         lines=lines,
                         delete_after=delete_after,
                         callback_next=callback_next,
                         callback_prev=callback_prev,
                         elements_per_page=elements_per_page)
        self.callback_element_selection = callback_element_selection

    async def update_menu(self, context: ComponentContext = None, message: ComponentMessage = None):
        for line in self.lines:
            reaction = line.retrieve_button("element_select")
            if reaction is not None:
                # Create the elements selection
                elements_select_options = []
                for i in range(0, self.elements_per_page):
                    index = (self.offset * self.elements_per_page) + i
                    if index < len(self.elements):
                        elements_select_options.append(
                            create_select_option(f"{self.elements[index]}", value=f"{index}"))
                    else:
                        break

                if len(elements_select_options) > 0:  # if we don't have elements or only one, we don't display it
                    element_select = create_select(options=elements_select_options,
                                                   placeholder="Select an element",
                                                   custom_id="element_select")
                    reaction.button = element_select
                else:
                    reaction.button["disabled"] = True
                break
        await super().update_menu(context=context, message=message)

    async def element_selected(self, **t):
        if self.callback_element_selection is not None:
            selected_option = int(t["context"].selected_options[0])
            selected_element = self.retrieve_element(selected_option)
            if selected_element is not None:
                await self.callback_element_selection(context=t["context"],
                                                      menu=t["menu"],
                                                      selected_index=selected_option,
                                                      selected_element=selected_element)
