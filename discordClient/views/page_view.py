from typing import Any, List
import math

from discord import User, Message, Emoji
from discord_slash.context import InteractionContext
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


class ViewWithReactions(Disposable):

    def __init__(self, puppet_bot, elements_to_display: Any, render: EmbedRender,
                 bound_to: User = None, reactions=None,
                 delete_after: int = None):
        self.puppet_bot = puppet_bot
        self.elements = elements_to_display
        self.render = render
        self.bound_to = bound_to
        self.reactions = reactions
        self.delete_after = delete_after
        self.menu_msg = None
        self.hidden_data = None

    def dispose(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_reaction_listener(self.menu_msg.id)

    def set_hidden_data(self, hidden_data: Any):
        self.hidden_data = hidden_data

    def retrieve_hidden_data(self) -> Any:
        return self.hidden_data

    async def display_menu(self, context: InteractionContext) -> Message:

        buttons = []
        for reaction in self.reactions:
            buttons.append(reaction.button)

        self.menu_msg = await context.send(content=self.render.generate_content(),
                                           embed=self.render.generate_render(self.elements),
                                           components=create_actionrow(*buttons))

        if self.menu_msg is not None:
            self.puppet_bot.append_delete_listener(DeleteListener(message=self.menu_msg,
                                                                  disposable_object=self))

        if self.reactions is not None:
            for reaction in self.reactions:
                self.puppet_bot.append_reaction_listener(ReactionListener(reaction.event_type,
                                                                          reaction.emojis,
                                                                          self.reaction_callback,
                                                                          self.menu_msg,
                                                                          bound_to=self.bound_to,
                                                                          return_emoji=True))
                for emoji in reaction.emojis:
                    await self.menu_msg.add_reaction(emoji)

        return self.menu_msg

    async def update_menu(self):
        await self.menu_msg.edit(content=self.render.generate_content(),
                                 embed=self.render.generate_render(self.elements))

    def update_datas(self, elements_to_display: list = None, render: EmbedRender = None):
        if elements_to_display is not None:
            self.elements = elements_to_display
        if render is not None:
            self.render = render

    def retrieve_reaction(self, emoji: Emoji) -> Reaction:
        for reaction in self.reactions:
            if emoji in reaction.emojis:
                return reaction
        return None

    def remove_reaction(self, emoji: Emoji):
        for reaction in self.reactions:
            if emoji in reaction.emojis:
                self.reactions.remove(reaction)

    async def reaction_callback(self, component_id: str, user_that_reacted: User):
        for reaction in self.reactions:
            if reaction.button["custom_id"] == component_id:
                await reaction.callback(self, user_that_reacted)


class PageView(ViewWithReactions):

    def __init__(self, puppet_bot, elements_to_display: list, render: ListEmbedRender,
                 bound_to: User = None, reactions: List[Reaction] = None,
                 delete_after: int = None,
                 callback_prev=None, callback_next=None, elements_per_page: int = 1):
        if reactions is not None:
            reactions = reactions.copy()
        else:
            reactions = []

        next_button = create_button(
            style=ButtonStyle.blue,
            label="Next page",
            custom_id="next_page",
            emoji=constants.RIGHT_ARROW_EMOJI
        )

        page_select_options = []
        for i in range(0, math.ceil(len(elements_to_display) / elements_per_page)):
            page_select_options.append(create_select_option(f"Page #{i + 1}", value=i))

        page_select = create_select(options=page_select_options,
                                    placeholder="Select the page you want to go to",
                                    min_values=1,
                                    max_values=1)

        previous_button = create_button(
            style=ButtonStyle.blue,
            label="Previous page",
            custom_id="previous_page",
            emoji=constants.LEFT_ARROW_EMOJI
        )

        reactions.insert(0, Reaction(button=next_button,
                                     callback=self.next_page))
        reactions.insert(0, Reaction(button=page_select,
                                     callback=self.next_page))
        reactions.insert(0, Reaction(button=previous_button,
                                     callback=self.previous_page))

        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         reactions=reactions,
                         delete_after=delete_after)
        self.elements_per_page = elements_per_page
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.offset = 0

    async def display_menu(self, context: InteractionContext) -> Message:
        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.offset * self.elements_per_page:
                                                (self.offset + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.offset]

        content = self.render.generate_content()
        embed = self.render.generate_render(elements_to_display, self.offset, self.offset * self.elements_per_page)

        buttons = []
        for reaction in self.reactions:
            buttons.append(reaction.button)
        components = [create_actionrow(*buttons)]

        self.menu_msg = await context.send(content=content, embed=embed, components=components)

        if self.menu_msg is not None:
            self.puppet_bot.append_delete_listener(DeleteListener(message=self.menu_msg,
                                                                  disposable_object=self))

        if self.reactions is not None:
            for reaction in self.reactions:
                self.puppet_bot.append_reaction_listener(ReactionListener(self.reaction_callback,
                                                                          self.menu_msg,
                                                                          interaction_id=reaction.button["custom_id"],
                                                                          bound_to=self.bound_to))

        return self.menu_msg

    async def update_menu(self):
        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.offset * self.elements_per_page:
                                                (self.offset + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.offset]
        await self.menu_msg.edit(content=self.render.generate_content(),
                                 embed=self.render.generate_render(elements_to_display, self.offset,
                                                                   self.offset * self.elements_per_page))

    def update_datas(self, elements_to_display: list = None, render: EmbedRender = None,
                     elements_per_page: int = None):
        super().update_datas(elements_to_display=elements_to_display,
                             render=render)
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page
        self.offset = 0

    async def next_page(self, triggered_menu: ViewWithReactions, user_that_reacted: User):
        self.offset += 1
        if self.offset * self.elements_per_page >= len(self.elements):
            self.offset -= 1
            return
        await self.update_menu()
        if self.callback_next is not None:
            self.callback_next(triggered_menu, user_that_reacted)

    async def previous_page(self, triggered_menu: ViewWithReactions, user_that_reacted: User):
        self.offset -= 1
        if self.offset < 0:
            self.offset = 0
            return
        await self.update_menu()
        if self.callback_prev is not None:
            self.callback_prev(triggered_menu, user_that_reacted)

    def retrieve_element(self, index):
        if index < len(self.elements):
            return self.elements[index]
        return None

    def retrieve_element_by_offset(self, offset: int):
        return self.retrieve_element(self.retrieve_index(offset))

    def retrieve_index(self, offset: int = 0) -> int:
        return self.offset * self.elements_per_page + offset


class PageView123(PageView):

    def __init__(self, puppet_bot,
                 elements_to_display: list, render: EmbedRender,
                 bound_to: User = None,
                 reactions: List[Reaction] = [], delete_after: int = None,
                 callback_prev=None, callback_next=None, elements_per_page: int = 1,
                 callback_number=None):
        reactions = reactions.copy()

        cre

        reactions.append(Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                  emojis=constants.NUMBER_EMOJIS[1:],
                                  callback=self.number_selected))

        super().__init__(puppet_bot=puppet_bot,
                         elements_to_display=elements_to_display,
                         render=render,
                         bound_to=bound_to,
                         reactions=reactions,
                         delete_after=delete_after,
                         callback_next=callback_next,
                         callback_prev=callback_prev,
                         elements_per_page=elements_per_page)
        self.callback_number = callback_number

    async def number_selected(self, triggered_menu: ViewWithReactions,
                              user_that_reacted: User, emoji_used: Emoji):
        if self.callback_number is not None:
            await self.callback_number(triggered_menu, user_that_reacted, emoji_used)
