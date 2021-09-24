from typing import Any, List

from discord import User, Message, Emoji
from discord.abc import Messageable

from discordClient.helper import constants
from discordClient.helper import Disposable, ReactionListener, DeleteListener
from discordClient.views.renders import EmbedRender, ListEmbedRender


class Reaction:

    def __init__(self, event_type, emojis, callback):
        if type(event_type) is not list:
            self.event_type = [event_type]
        else:
            self.event_type = event_type
        if type(emojis) is not list:
            self.emojis = [emojis]
        else:
            self.emojis = emojis
        self.callback = callback


class ViewWithReactions(Disposable):

    def __init__(self, puppet_bot, elements_to_display: Any, render: EmbedRender,
                 bound_to: User = None, reactions: List[Reaction] = None,
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

    async def display_menu(self, context: Messageable) -> Message:
        self.menu_msg = await context.send(content=self.render.generate_content(),
                                           embed=self.render.generate_render(self.elements))

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

    async def reaction_callback(self, user_that_reacted: User, emoji_used: Emoji):
        string_emoji = emoji_used.name
        for reaction in self.reactions:
            if string_emoji in reaction.emojis:
                await reaction.callback(self, user_that_reacted, emoji_used)


class PageView(ViewWithReactions):

    def __init__(self, puppet_bot, elements_to_display: list, render: ListEmbedRender,
                 bound_to: User = None, reactions: List[Reaction] = None,
                 delete_after: int = None,
                 callback_prev=None, callback_next=None, elements_per_page: int = 1):
        if reactions is not None:
            reactions = reactions.copy()
        else:
            reactions = []
        reactions.insert(0, Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                     emojis=constants.RIGHT_ARROW_EMOJI,
                                     callback=self.next_page))
        reactions.insert(0, Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                     emojis=constants.LEFT_ARROW_EMOJI,
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

    async def display_menu(self, context: Messageable) -> Message:
        if self.elements_per_page > 1:
            elements_to_display = self.elements[self.offset * self.elements_per_page:
                                                (self.offset + 1) * self.elements_per_page]
        else:
            elements_to_display = self.elements[self.offset]

        self.menu_msg = await context.send(content=self.render.generate_content(),
                                           embed=self.render.generate_render(elements_to_display, self.offset,
                                                                             self.offset * self.elements_per_page))

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

    async def next_page(self, triggered_menu: ViewWithReactions,
                        user_that_reacted: User, emoji_used: Emoji):
        self.offset += 1
        if self.offset * self.elements_per_page >= len(self.elements):
            self.offset -= 1
            return
        await self.update_menu()
        if self.callback_next is not None:
            self.callback_next(triggered_menu, user_that_reacted)

    async def previous_page(self, triggered_menu: ViewWithReactions,
                            user_that_reacted: User, emoji_used: Emoji):
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
