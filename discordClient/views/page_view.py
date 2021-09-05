import asyncio

from discord import Embed, User, Message, Emoji
from discord.abc import Messageable

from discordClient.helper import constants
from discordClient.helper.reaction_listener import ReactionListener


class PageView:

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list, elements_per_page: int,
                 callback_prev=None, callback_next=None,
                 bound_to: User = None):
        self.puppet_bot = puppet_bot
        self.menu_title = menu_title
        self.elements = elements_to_display
        self.elements_per_page = elements_per_page
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.bound_to = bound_to
        self.offset = 0
        self.menu_msg = None

    def __del__(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_listener(self.menu_msg.id)

    async def display_menu(self, context: Messageable) -> Message:
        menu_embed = self.generate_embed()

        self.menu_msg = await context.send(embed=menu_embed)
        await self.menu_msg.add_reaction(constants.LEFT_ARROW_EMOJI)
        await self.menu_msg.add_reaction(constants.RIGHT_ARROW_EMOJI)

        # Previous listener
        self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                         constants.LEFT_ARROW_EMOJI,
                                                         self.previous_page,
                                                         self.menu_msg.id,
                                                         bound_to=self.bound_to))

        # Next listener
        self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                         constants.RIGHT_ARROW_EMOJI,
                                                         self.next_page,
                                                         self.menu_msg.id,
                                                         bound_to=self.bound_to))

        return self.menu_msg

    async def update_menu(self):
        await self.menu_msg.edit(embed=self.generate_embed())

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     elements_per_page: int = None):
        if menu_title is not None:
            self.menu_title = menu_title
        if elements_to_display is not None:
            self.elements = elements_to_display
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page

    def generate_embed(self):
        menu_embed = Embed()
        description = ""
        iteration = 1
        for element in self.elements[self.offset * self.elements_per_page:(self.offset + 1) * self.elements_per_page]:
            description += f"`{(self.offset * self.elements_per_page) + iteration}`. {element}\n"
            iteration += 1

        if self.bound_to is not None:
            menu_embed.set_author(name=f"{self.bound_to.name}#{self.bound_to.discriminator}",
                                  icon_url=self.bound_to.avatar_url)
        menu_embed.title = self.menu_title
        menu_embed.description = description
        menu_embed.set_footer(text=f"Page: {self.offset + 1}")
        return menu_embed

    async def next_page(self, user_that_reacted: User):
        self.offset += 1
        if self.offset * self.elements_per_page > len(self.elements):
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


class PageModelView(PageView):

    def __init__(self, puppet_bot, elements_to_display: list,
                 callback_prev=None, callback_next=None,
                 bound_to: User = None):
        super().__init__(puppet_bot, "", elements_to_display, 1,
                         callback_prev, callback_next, bound_to)

    def generate_embed(self):
        menu_embed = self.elements[self.offset].__repr__()
        footer_proxy = menu_embed.footer
        menu_embed.set_footer(text=f"{footer_proxy.text} | Page: {self.offset + 1}",
                              icon_url=footer_proxy.icon_url)
        return menu_embed


class Page123View(PageView):

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list, elements_per_page: int,
                 callback_letter, callback_prev=None, callback_next=None,
                 bound_to: User = None):
        super().__init__(puppet_bot, menu_title, elements_to_display, elements_per_page,
                         callback_prev, callback_next, bound_to)
        self.lock = asyncio.Lock()
        self.callback_letter = callback_letter

    async def display_menu(self, context: Messageable):
        async with self.lock:
            await super().display_menu(context)
            letters_to_display = constants.NUMBER_EMOJIS[(self.offset * self.elements_per_page) + 1:
                                                         ((self.offset + 1) * self.elements_per_page) + 1]

            self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                             letters_to_display,
                                                             self.letter_selected,
                                                             self.menu_msg.id,
                                                             bound_to=self.bound_to,
                                                             return_emoji=True))
            for letter in letters_to_display:
                await self.menu_msg.add_reaction(letter)

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     elements_per_page: int = None, callback_letter=None):
        super().update_datas(menu_title, elements_to_display, elements_per_page)
        if callback_letter is not None:
            self.callback_letter = callback_letter

    async def letter_selected(self, user_that_reacted: User, emoji_used: Emoji):
        if self.callback_letter is not None:
            async with self.lock:
                await self.callback_letter(self, user_that_reacted, emoji_used)


class Page123AndAllView(Page123View):

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list, elements_per_page: int,
                 callback_letter, callback_all, callback_prev=None, callback_next=None,
                 bound_to: User = None):
        super().__init__(puppet_bot, menu_title, elements_to_display, elements_per_page,
                         callback_letter, callback_prev, callback_next, bound_to)
        self.callback_all = callback_all

    async def display_menu(self, context: Messageable):
        await super().display_menu(context)
        self.puppet_bot.append_listener(ReactionListener([constants.REACTION_ADD, constants.REACTION_REMOVE],
                                                         constants.ASTERISK_EMOJI,
                                                         self.all_selected,
                                                         self.menu_msg.id,
                                                         bound_to=self.bound_to))
        await self.menu_msg.add_reaction(constants.ASTERISK_EMOJI)

    def generate_embed(self):
        menu_embed = super().generate_embed()
        description = ""
        iteration = 1
        for element in self.elements[self.offset * self.elements_per_page:(self.offset + 1) * self.elements_per_page]:
            description += f"{constants.NUMBER_EMOJIS[iteration]} • \t{element}\n"
            iteration += 1

        if self.callback_all is not None:
            description += f"{constants.ASTERISK_EMOJI} • Display all"
        menu_embed.description = description
        return menu_embed

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     elements_per_page: int = None, callback_letter=None, callback_all=None):
        super().update_datas(menu_title, elements_to_display, elements_per_page, callback_letter)
        if callback_all is not None:
            self.callback_all = callback_all

    async def all_selected(self, user_that_reacted: User):
        if self.callback_all is not None:
            async with self.lock:
                await self.callback_all(self, user_that_reacted)
