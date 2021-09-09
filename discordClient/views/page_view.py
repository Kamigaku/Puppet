import asyncio
from typing import Any

from discord import Embed, User, Message, Emoji
from discord.abc import Messageable

from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener

class PageView:

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list, elements_per_page: int,
                 author: User = None,
                 callback_prev=None, callback_next=None,
                 bound_to: User = None, msg_content: str = None,
                 reset_counter_on_each_page: bool = False):
        self.puppet_bot = puppet_bot
        self.menu_title = menu_title
        self.elements = elements_to_display
        self.elements_per_page = elements_per_page
        self.author = author
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.bound_to = bound_to
        self.offset = 0
        self.menu_msg = None
        self.hidden_data = None
        self.msg_content = msg_content
        self.reset_counter_on_each_page = reset_counter_on_each_page

    def __del__(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_listener(self.menu_msg.id)

    def set_hidden_data(self, hidden_data: Any):
        self.hidden_data = hidden_data

    def retrieve_hidden_data(self) -> Any:
        return self.hidden_data

    async def display_menu(self, context: Messageable) -> Message:
        menu_embed = self.generate_embed()

        if self.msg_content is not None:
            self.menu_msg = await context.send(content=self.msg_content, embed=menu_embed)
        else:
            self.menu_msg = await context.send(embed=menu_embed)
        await self.menu_msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        await self.menu_msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

        # Previous listener
        self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                         constants.LEFT_ARROW_EMOJI,
                                                         self.previous_page,
                                                         self.menu_msg,
                                                         bound_to=self.bound_to))

        # Next listener
        self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                         constants.RIGHT_ARROW_EMOJI,
                                                         self.next_page,
                                                         self.menu_msg,
                                                         bound_to=self.bound_to))

        return self.menu_msg

    async def update_menu(self):
        await self.menu_msg.edit(content=self.msg_content, embed=self.generate_embed())

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     elements_per_page: int = None, author: User = None, msg_content: str = None,
                     reset_counter_on_each_page: bool = None):
        if menu_title is not None:
            self.menu_title = menu_title
        if elements_to_display is not None:
            self.elements = elements_to_display
            self.offset = 0
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page
            self.offset = 0
        if author is not None:
            self.author = author
            self.offset = 0
        if msg_content is not None:
            self.msg_content = msg_content
        if reset_counter_on_each_page is not None:
            self.reset_counter_on_each_page = reset_counter_on_each_page
            self.offset = 0

    def generate_embed(self):
        menu_embed = Embed()
        description = ""
        iteration = 1
        for element in self.elements[self.offset * self.elements_per_page:(self.offset + 1) * self.elements_per_page]:
            description += "`"
            if self.reset_counter_on_each_page:
                description += f"{iteration}"
            else:
                description += f"{(self.offset * self.elements_per_page) + iteration}"
            description += f"`. {element}\n"
            iteration += 1

        if self.author is not None:
            menu_embed.set_author(name=f"{self.author.name}#{self.author.discriminator}",
                                  icon_url=self.author.avatar_url)
        menu_embed.title = self.menu_title
        menu_embed.description = description
        menu_embed.set_footer(text=f"Page: {self.offset + 1}")
        return menu_embed

    async def next_page(self, user_that_reacted: User):
        self.offset += 1
        if self.offset * self.elements_per_page >= len(self.elements):
            self.offset -= 1
            return
        await self.update_menu()
        if self.callback_next is not None:
            self.callback_next(self, user_that_reacted)

    async def previous_page(self, user_that_reacted: User):
        self.offset -= 1
        if self.offset < 0:
            self.offset = 0
            return
        await self.update_menu()
        if self.callback_prev is not None:
            self.callback_prev(self, user_that_reacted)

    def retrieve_element(self, index):
        return self.elements[index]

    def retrieve_element_by_offset(self, offset: int):
        return self.retrieve_element(self.offset * self.elements_per_page + offset)


class PageReaction:

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


class PageViewWithReactions(PageView):

    def __init__(self, puppet_bot, menu_title: str, elements_to_display: list, elements_per_page: int,
                 reactions: list[PageReaction] = None,
                 author: User = None, callback_prev=None, callback_next=None,
                 bound_to: User = None, msg_content: str = None):
        super().__init__(puppet_bot=puppet_bot,
                         menu_title=menu_title,
                         elements_to_display=elements_to_display,
                         elements_per_page=elements_per_page,
                         author=author,
                         callback_prev=callback_prev,
                         callback_next=callback_next,
                         bound_to=bound_to,
                         msg_content=msg_content)
        self.reactions = reactions

    async def display_menu(self, context: Messageable) -> Message:
        await super().display_menu(context)
        for reaction in self.reactions:
            self.puppet_bot.append_listener(ReactionListener(reaction.event_type,
                                                             reaction.emojis,
                                                             self.reaction_callback,
                                                             self.menu_msg,
                                                             bound_to=self.bound_to,
                                                             return_emoji=True))
            for emoji in reaction.emojis:
                await self.menu_msg.add_reaction(emoji)
        return self.menu_msg

    async def reaction_callback(self, user_that_reacted: User, emoji_used: Emoji):
        string_emoji = emoji_used.name
        for reaction in self.reactions:
            if string_emoji in reaction.emojis:
                await reaction.callback(self, user_that_reacted, emoji_used)

    def retrieve_reaction(self, emoji: Emoji) -> PageReaction:
        for reaction in self.reactions:
            if emoji in reaction.emojis:
                return reaction
        return None


class PageModelView(PageViewWithReactions):

    def __init__(self, puppet_bot, elements_to_display: list,
                 reactions: list[PageReaction] = None,
                 callback_prev=None, callback_next=None,
                 bound_to: User = None, author: User = None, msg_content: str = None):
        super().__init__(puppet_bot=puppet_bot,
                         menu_title="",
                         elements_to_display=elements_to_display,
                         elements_per_page=1,
                         author=author,
                         callback_prev=callback_prev,
                         callback_next=callback_next,
                         bound_to=bound_to,
                         msg_content=msg_content,
                         reactions=reactions)

    def generate_embed(self):
        menu_embed = self.elements[self.offset].__repr__()
        footer_proxy = menu_embed.footer
        menu_embed.set_footer(text=f"{footer_proxy.text} | Page: {self.offset + 1}",
                              icon_url=footer_proxy.icon_url)
        return menu_embed
