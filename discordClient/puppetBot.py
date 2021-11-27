import logging
import typing

from discord import Intents, RawMessageDeleteEvent, User
from discord.ext.commands import Bot, Cog
from discord_slash import SlashCommand, ComponentContext

from discordClient.cogs.announcement_cogs import AnnouncementCogs
from discordClient.cogs.event_cogs import EventCogs
from discordClient.cogs.settings_cogs import SettingsCogs
from discordClient.cogs.card_cogs import CardCogs
from discordClient.cogs.economy_cogs import EconomyCogs
from discordClient.cogs.museum_cogs import MuseumCogs
from discordClient.cogs.report_cogs import ReportCogs
from discordClient.cogs.trade_cogs import TradeCogs

from discordClient.helper.listener import ReactionListener, DeleteListener


class PuppetBot(Bot):

    def __init__(self, commands_prefix: str, debug_mode: bool = False, sync_commands: bool = False):
        intents = Intents.default()
        intents.members = True
        intents.presences = True
        intents.reactions = True
        super().__init__(command_prefix=commands_prefix, intents=intents,
                         self_bot=True)
        if not debug_mode:
            self.slash = SlashCommand(self, sync_commands=sync_commands)
        else:
            self.slash = SlashCommand(self, sync_commands=sync_commands, debug_guild=877098506211442719)
            #self.slash = SlashCommand(self, sync_commands=sync_commands, debug_guild=877098506211442719)
        self.reaction_listeners = {}
        self.delete_listeners = {}

        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

        logger = logging.getLogger('discord')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger = logging.getLogger('discord_slash')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger = logging.getLogger('peewee')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger = logging.getLogger('puppet')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        self.logger = logger
        self.logger.info("Puppet is online!")
        print("Puppet is online!")

    def default_initialisation(self):
        self.add_cog(EconomyCogs(self))
        self.add_cog(CardCogs(self))
        self.add_cog(MuseumCogs(self))
        self.add_cog(ReportCogs(self))
        self.add_cog(TradeCogs(self))
        self.add_cog(AnnouncementCogs(self))
        self.add_cog(SettingsCogs(self))
        #self.add_cog(EventCogs(self))

    def append_reaction_listener(self, reaction_listener: ReactionListener):
        if reaction_listener.message.id not in self.reaction_listeners:
            self.reaction_listeners[reaction_listener.message.id] = []
        self.reaction_listeners[reaction_listener.message.id].append(reaction_listener)

    def remove_reaction_listener(self, message_id: int):
        if message_id in self.reaction_listeners:
            self.logger.info(f"Removing the listener for the message id {message_id}")
            self.reaction_listeners.pop(message_id)

    def append_delete_listener(self, delete_listener: DeleteListener):
        if delete_listener.message.id not in self.delete_listeners:
            self.delete_listeners[delete_listener.message.id] = delete_listener

    def execute_delete_listener(self, message_id: int):
        self.logger.info(f"Disposing the message id {message_id}")
        self.delete_listeners[message_id].dispose()
        self.delete_listeners.pop(message_id)

    @staticmethod
    def get_common_users(user: User) -> typing.List:
        mutual_guilds = user.mutual_guilds
        active_ids = []
        for mutual_guild in mutual_guilds:
            for member in mutual_guild.members:
                if member.id not in active_ids:
                    active_ids.append(member)
        return active_ids

    ################################
    #       LISTENERS BOT          #
    ################################

    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        if payload.message_id in self.delete_listeners:
            self.execute_delete_listener(payload.message_id)

    async def on_component(self, ctx: ComponentContext):
        if self.user.id != ctx.author.id and ctx.origin_message_id in self.reaction_listeners:
            user_that_reacted = None
            message_listener = self.reaction_listeners[ctx.origin_message_id]
            for reaction_listener in message_listener:
                if (reaction_listener.interaction_id == ctx.component_id and
                        (reaction_listener.bound_to is None or
                         (reaction_listener.bound_to is not None and reaction_listener.bound_to == ctx.author_id))):
                    # Retrieve user
                    if user_that_reacted is None:
                        user_that_reacted = self.get_user(ctx.author_id)
                        if user_that_reacted is None:
                            user_that_reacted = await self.fetch_user(ctx.author_id)
                        if user_that_reacted.bot:
                            return
                    await reaction_listener.callback(context=ctx,
                                                     user_that_interact=user_that_reacted)

    # async def on_slash_command(self, ctx: ComponentContext):
    #     if isinstance(ctx.cog, AssignableCogs):
    #         if not ctx.cog.check_assignation():
    #             # await ctx.send(content="Your command have to be sent in the channel assigned to it.",
    #             #                hidden=True)
    #             return
