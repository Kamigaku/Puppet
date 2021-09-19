from typing import Any, List

from discord import Embed, User, Message, Emoji
from discord.abc import Messageable

from discordClient.helper import constants
from discordClient.helper.disposable import Disposable
from discordClient.helper.listener import ReactionListener, DeleteListener


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


class Fields:

    def __init__(self, title: str, data: list, inline: bool = True):
        self.title = title
        self.data = data
        self.inline = inline


class ViewWithReactions(Disposable):

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list,
                 author: User = None, bound_to: User = None, msg_content: str = None,
                 reactions: List[Reaction] = None, delete_after: int = None,
                 fields: List[Fields] = None, thumbnail: str = None):
        self.puppet_bot = puppet_bot
        self.menu_title = menu_title
        self.elements = elements_to_display
        self.author = author
        self.bound_to = bound_to
        self.menu_msg = None
        self.hidden_data = None
        self.msg_content = msg_content
        self.reactions = reactions
        self.delete_after = delete_after
        self.fields = fields
        self.thumbnail = thumbnail

    def dispose(self):
        if self.menu_msg is not None:
            self.puppet_bot.remove_reaction_listener(self.menu_msg.id)

    def set_hidden_data(self, hidden_data: Any):
        self.hidden_data = hidden_data

    def retrieve_hidden_data(self) -> Any:
        return self.hidden_data

    async def display_menu(self, context: Messageable) -> Message:
        menu_embed = self.generate_embed()

        if self.msg_content is not None:
            self.menu_msg = await context.send(content=self.msg_content,
                                               embed=menu_embed,
                                               delete_after=self.delete_after)
        else:
            self.menu_msg = await context.send(embed=menu_embed,
                                               delete_after=self.delete_after)

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

    def generate_embed(self) -> Embed:
        menu_embed = Embed()
        if self.author is not None:
            menu_embed.set_author(name=f"{self.author.name}#{self.author.discriminator}",
                                  icon_url=self.author.avatar_url)
        menu_embed.title = self.menu_title
        menu_embed.description = self.generate_description()
        if self.fields is not None:
            if type(self.fields) is list:
                current_field = self.fields[self.offset]
            else:
                current_field = self.fields

            for field in current_field:
                menu_embed.add_field(name=field.title,
                                     value=field.data,
                                     inline=field.inline)
        if self.thumbnail is not None:
            menu_embed.set_thumbnail(url=self.thumbnail)
        return menu_embed

    def generate_description(self) -> str:
        description = ""
        for element in self.elements:
            description += f"{element}\n"
        return description

    async def update_menu(self):
        await self.menu_msg.edit(content=self.msg_content, embed=self.generate_embed())

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     author: User = None, msg_content: str = None, fields: List[Fields] = None):
        if menu_title is not None:
            self.menu_title = menu_title
        if elements_to_display is not None:
            self.elements = elements_to_display
        if author is not None:
            self.author = author
        if msg_content is not None:
            self.msg_content = msg_content
        if fields is not None:
            self.fields = fields

    def retrieve_element(self, index):
        if index < len(self.elements):
            return self.elements[index]
        return None

    def retrieve_reaction(self, emoji: Emoji) -> Reaction:
        for reaction in self.reactions:
            if emoji in reaction.emojis:
                return reaction
        return None

    def retrieve_fields(self) -> List[Fields]:
        return self.fields

    def retrieve_field(self, index: int) -> Fields:
        if index < len(self.fields):
            return self.fields[index]
        return None

    async def reaction_callback(self, user_that_reacted: User, emoji_used: Emoji):
        string_emoji = emoji_used.name
        for reaction in self.reactions:
            if string_emoji in reaction.emojis:
                await reaction.callback(self, user_that_reacted, emoji_used)


class PageView(ViewWithReactions):

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list,
                 author: User = None, bound_to: User = None, msg_content: str = None,
                 reactions: List[Reaction] = [], delete_after: int = None,
                 callback_prev=None, callback_next=None, elements_per_page: int = 1,
                 fields: List[Fields] = None, thumbnail: str = None):
        reactions = reactions.copy()
        reactions.insert(0, Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                     emojis=constants.RIGHT_ARROW_EMOJI,
                                     callback=self.next_page))
        reactions.insert(0, Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                     emojis=constants.LEFT_ARROW_EMOJI,
                                     callback=self.previous_page))

        super(PageView, self).__init__(puppet_bot=puppet_bot,
                                       menu_title=menu_title,
                                       elements_to_display=elements_to_display,
                                       author=author,
                                       bound_to=bound_to,
                                       msg_content=msg_content,
                                       reactions=reactions,
                                       delete_after=delete_after,
                                       fields=fields,
                                       thumbnail=thumbnail)
        self.elements_per_page = elements_per_page
        self.callback_prev = callback_prev
        self.callback_next = callback_next
        self.offset = 0

    def update_datas(self, menu_title: str = None, elements_to_display: list = None,
                     elements_per_page: int = None, author: User = None, msg_content: str = None):
        super(PageView, self).update_datas(menu_title=menu_title,
                                           elements_to_display=elements_to_display,
                                           author=author,
                                           msg_content=msg_content)
        if elements_per_page is not None:
            self.elements_per_page = elements_per_page
        self.offset = 0

    def generate_embed(self) -> Embed:
        menu_embed = super(PageView, self).generate_embed()
        menu_embed.set_footer(text=f"Page: {self.offset + 1}")
        return menu_embed

    def generate_description(self) -> str:
        description = ""
        iteration = 1
        for element in self.elements[self.offset * self.elements_per_page:(self.offset + 1) * self.elements_per_page]:
            description += f"`{(self.offset * self.elements_per_page) + iteration}`. {element}\n"
            iteration += 1
        return description

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

    def retrieve_element_by_offset(self, offset: int):
        return self.retrieve_element(self.retrieve_index(offset))

    def retrieve_index(self, offset: int = 0) -> int:
        return self.offset * self.elements_per_page + offset


class PageView123(PageView):

    def __init__(self, puppet_bot,
                 menu_title: str, elements_to_display: list,
                 author: User = None, bound_to: User = None, msg_content: str = None,
                 reactions: List[Reaction] = [], delete_after: int = None,
                 callback_prev=None, callback_next=None, elements_per_page: int = 1,
                 fields: List[Fields] = None, thumbnail: str = None,
                 callback_number=None):
        reactions = reactions.copy()
        reactions.append(Reaction(event_type=[constants.REACTION_ADD, constants.REACTION_REMOVE],
                                  emojis=constants.NUMBER_EMOJIS[1:],
                                  callback=self.number_selected))

        super(PageView123, self).__init__(puppet_bot=puppet_bot,
                                          menu_title=menu_title,
                                          elements_to_display=elements_to_display,
                                          author=author,
                                          bound_to=bound_to,
                                          msg_content=msg_content,
                                          reactions=reactions,
                                          delete_after=delete_after,
                                          fields=fields,
                                          thumbnail=thumbnail,
                                          callback_next=callback_next,
                                          callback_prev=callback_prev,
                                          elements_per_page=elements_per_page)
        self.callback_number = callback_number

    def generate_description(self) -> str:
        description = ""
        iteration = 1
        for element in self.elements[self.offset * self.elements_per_page:(self.offset + 1) * self.elements_per_page]:
            description += f"{constants.NUMBER_EMOJIS[iteration]} • {element}\n"
            iteration += 1
        return description

    async def number_selected(self, triggered_menu: ViewWithReactions,
                              user_that_reacted: User, emoji_used: Emoji):
        if self.callback_number is not None:
            await self.callback_number(triggered_menu, user_that_reacted, emoji_used)


class PageModelView(PageView):

    def __init__(self, puppet_bot, elements_to_display: list, menu_title: str = "",
                 reactions: List[Reaction] = [], delete_after: int = None,
                 callback_prev=None, callback_next=None,
                 bound_to: User = None, author: User = None, msg_content: str = None,
                 fields: List[Fields] = None, thumbnail: str = None):
        super(PageModelView, self).__init__(puppet_bot=puppet_bot,
                                            menu_title=menu_title,
                                            elements_to_display=elements_to_display,
                                            elements_per_page=1,
                                            author=author,
                                            callback_prev=callback_prev,
                                            callback_next=callback_next,
                                            bound_to=bound_to,
                                            msg_content=msg_content,
                                            reactions=reactions,
                                            delete_after=delete_after,
                                            fields=fields,
                                            thumbnail=thumbnail)

    def generate_embed(self):
        if type(self.elements) is list:
            menu_embed = self.elements[self.offset].__repr__()
            footer_proxy = menu_embed.footer
            menu_embed.set_footer(text=f"{footer_proxy.text} | Page: {self.offset + 1}",
                                  icon_url=footer_proxy.icon_url)
            if self.fields is not None:
                if type(self.fields) is list:
                    current_field = self.fields[self.offset]
                else:
                    current_field = self.fields

                for field in current_field:
                    menu_embed.add_field(name=field.title,
                                         value=field.data,
                                         inline=field.inline)
            return menu_embed
        else:
            return self.elements.__repr__()

        # working
        # menu_embed = self.elements[self.offset].__repr__()
        # footer_proxy = menu_embed.footer
        # menu_embed.set_footer(text=f"{footer_proxy.text} | Page: {self.offset + 1}",
        #                       icon_url=footer_proxy.icon_url)
        return menu_embed
