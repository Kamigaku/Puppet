import inspect
import logging

from discord.ext import commands
from discord import Intents, RawReactionActionEvent, RawMessageDeleteEvent

from discordClient.cogs.cardCogs import CardCogs
from discordClient.cogs.economyCogs import EconomyCogs
from discordClient.cogs.museumCogs import MuseumCogs
from discordClient.cogs.report_cogs import ReportCogs
from discordClient.cogs.trade_cogs import TradeCogs
from discordClient.helper.listener import ReactionListener, DeleteListener


class PuppetBot(commands.Bot):

    def __init__(self, commands_prefix: str):
        intents = Intents.default()
        intents.members = True
        intents.presences = True
        intents.reactions = True
        super().__init__(command_prefix=commands_prefix, intents=intents)
        self.reaction_listeners = {}
        self.delete_listeners = {}

        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

        logger = logging.getLogger('discord')
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

    def append_reaction_listener(self, reaction_listener: ReactionListener):
        if not inspect.ismethod(reaction_listener.callback) and not inspect.isfunction(reaction_listener.callback):
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" is not a function.")
        if not inspect.iscoroutinefunction(reaction_listener.callback):
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" is not a coroutine function.")
        number_arguments = len(inspect.getfullargspec(reaction_listener.callback).args)
        if 1 < number_arguments < 2:
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" must have 1 or 2 parameters.\n"
                              f"The parameters needs to be: user, [emoji].")
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

    ################################
    #       LISTENERS BOT          #
    ################################

    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self.on_raw_reaction(payload)

    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self.on_raw_reaction(payload)

    async def on_raw_reaction(self, payload: RawReactionActionEvent):
        if self.user.id == payload.user_id:  # We avoid to react to the current bot reactions
            return

        string_emoji = str(payload.emoji)

        if payload.message_id not in self.reaction_listeners:
            return
        else:
            message_listener = self.reaction_listeners[payload.message_id]

            for reaction_listener in message_listener:
                if (payload.event_type in reaction_listener.event_type and string_emoji in reaction_listener.emoji and
                        (reaction_listener.bound_to is None or
                         (reaction_listener.bound_to is not None and reaction_listener.bound_to == payload.user_id))):

                    # Retrieve user
                    user_that_reacted = self.get_user(payload.user_id)
                    if user_that_reacted is None:
                        user_that_reacted = await self.fetch_user(payload.user_id)
                    if user_that_reacted.bot:
                        return

                    if not reaction_listener.return_emoji:
                        await reaction_listener.callback(user_that_reacted)
                    else:
                        await reaction_listener.callback(user_that_reacted, payload.emoji)

    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        if payload.message_id in self.delete_listeners:
            self.logger.info(f"Disposing the message id {payload.message_id}")
            self.delete_listeners[payload.message_id].dispose()
            self.delete_listeners.pop(payload.message_id)
