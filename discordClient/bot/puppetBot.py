import re
import inspect
import logging

from discord.ext import commands
from discord import Intents, RawReactionActionEvent, Embed

from discordClient.cogs.cardCogs import CardCogs
from discordClient.cogs.economyCogs import EconomyCogs
from discordClient.cogs.museumCogs import MuseumCogs
from discordClient.cogs.report_cogs import ReportCogs
from discordClient.cogs.trade_cogs import TradeCogs
from discordClient.helper.reaction_listener import ReactionListener


class PuppetBot(commands.Bot):

    def __init__(self, commands_prefix: str):
        intents = Intents.default()
        intents.members = True
        intents.presences = True
        intents.reactions = True
        super().__init__(command_prefix=commands_prefix, intents=intents)
        self.reaction_listeners = []

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

    def default_initialisation(self):
        self.add_cog(EconomyCogs(self))
        self.add_cog(CardCogs(self))
        self.add_cog(MuseumCogs(self))
        self.add_cog(ReportCogs(self))
        self.add_cog(TradeCogs(self))

    def retrieve_puppet_id(self, embeds: Embed) -> int:
        puppet_id_str = self.retrieve_from_embed(embeds, "Puppet_id: (\d+)")
        if not puppet_id_str:
            return None
        return int(puppet_id_str)

    def retrieve_from_embed(self, embeds: Embed, pattern: str):
        if embeds is not None and len(embeds) > 0:
            for embed in embeds:
                if embed.footer is not None:
                    regex_result = re.search(pattern=pattern, string=embed.footer.text)
                    if regex_result:
                        return regex_result.group(1)
        return ""

    def append_listener(self, reaction_listener: ReactionListener):
        if not inspect.ismethod(reaction_listener.callback):
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" is not a function.")
        if not inspect.iscoroutinefunction(reaction_listener.callback):
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" is not a coroutine function.")
        number_arguments = len(inspect.getfullargspec(reaction_listener.callback).args)
        if 2 < number_arguments < 3:
            raise SyntaxError(f"The callback \"{reaction_listener.callback.__name__}\" must have 2 or 3 parameters.\n"
                              f"The parameters needs to be: message, user, [emoji].")
        self.reaction_listeners.append(reaction_listener)

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

        user_that_reacted = None
        origin_message = None
        puppet_id = None

        for reaction_listener in self.reaction_listeners:
            if payload.event_type in reaction_listener.event_type and string_emoji in reaction_listener.emoji:

                # Retrieve user
                if user_that_reacted is None:
                    user_that_reacted = self.get_user(payload.user_id)
                    if user_that_reacted is None:
                        user_that_reacted = await self.fetch_user(payload.user_id)
                    if user_that_reacted.bot:
                        return

                if origin_message is None:
                    channel_message = self.get_channel(payload.channel_id)
                    if channel_message is None:
                        channel_message = await self.fetch_channel(payload.channel_id)

                    # On pourrait ici ajouter un cache local au niveau du bot des messages de commands
                    origin_message = await channel_message.fetch_message(payload.message_id)

                if puppet_id is None:
                    puppet_id = self.retrieve_puppet_id(origin_message.embeds)

                if reaction_listener.puppet_id == -1 or reaction_listener.puppet_id == puppet_id:
                    if not reaction_listener.return_emoji:
                        await reaction_listener.callback(origin_message, user_that_reacted)
                    else:
                        await reaction_listener.callback(origin_message, user_that_reacted, payload.emoji)
                    if reaction_listener.remove_reaction:
                        origin_message.remove_reaction(payload.emoji, payload.user_id)
