import typing
from datetime import datetime, timedelta, timezone
import random

import discord
from discord.ext import tasks
from discord.ext.tasks import Loop
from discord_slash import SlashCommandOptionType, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice

from discordClient.cogs import announcement_cogs, card_cogs
from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import EventParticipants, CharactersOwnership, Economy, Character
from discordClient.model.event import Event
from discordClient.model.jointure_tables import EventRewards
from discordClient.views import ViewReactionsLine, GiveawayRender, ViewWithReactions, Reaction, EventResultRenderer, \
    GiveawayResultRender, PageView, CharactersOwnershipEmbedRender, CharacterListEmbedRender


class EventCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "event")
        self.event_loop.start()
        self.active_event = None

    # Decorators

    def event(func):
        async def wrapper(self, loop, event: Event, *args, **kwargs):
            result = await func(self, event, *args, **kwargs)
            if isinstance(loop, Loop):
                await discord.utils.sleep_until(event.start_time.replace(tzinfo=timezone.utc) +
                                                timedelta(minutes=event.duration))
                await self.complete_event(event)
            return result

        return wrapper

    # Slash commands

    @cog_ext.cog_slash(name="giveaway",
                       description="Start a giveaway event",
                       options=[
                           create_option(
                               name="duration",
                               description="Specify the duration, in minutes, of the event",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True
                           ),
                           create_option(
                               name="card_id",
                               description="Specify the card id that will be dropped",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=False
                           ),
                           create_option(
                               name="booster_amount",
                               description="Specify the amount of booster will be given",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=False
                           ),
                           create_option(
                               name="money_amount",
                               description="Specify the amount of money that will be given",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=False
                           ),
                           create_option(
                               name="format",
                               description="Specify the format of the giveaway",
                               option_type=SlashCommandOptionType.STRING,
                               choices=[create_choice(name="Random",
                                                      value="0"),
                                        create_choice(name="First",
                                                      value="1")],
                               required=False
                           ),
                           create_option(
                               name="winner_number",
                               description="Specify the amount of player that will win",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=False
                           ),
                           create_option(
                               name="guild_restriction",
                               description="Specify a guild id if you want to restrict the giveaway",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=False
                           )
                       ])
    @BaseCogs.moderator_restricted
    async def giveaway(self, ctx: SlashContext, duration: int, card_id: int = None, booster_amount: int = None,
                       money_amount: int = None, format: str = "0", winner_number: int = 1,
                       guild_restriction: int = -1):
        if winner_number < 1:
            await ctx.send("You need at least 1 winner for the event.", hidden=True)
            return
        if duration < 0:
            await ctx.send("The minutes you have entered is invalid. It should be a positive integer.", hidden=True)
            return
        event_model, reward_model = generate_event(duration=duration,
                                                   start_time=datetime.utcnow(),
                                                   card_id=card_id,
                                                   booster_amount=booster_amount,
                                                   money_amount=money_amount,
                                                   format_event=format,
                                                   winner_number=winner_number,
                                                   guild_restriction=guild_restriction,
                                                   started_by=ctx.author_id)
        await ctx.send("The giveaway has been created.", hidden=True)
        self.start_event(event_model)

    @cog_ext.cog_slash(name="event_cancel",
                       description="Cancel an active event with or without a specific message",
                       options=[
                           create_option(
                               name="event_id",
                               description="Specify the event id that will be cancel",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True
                           ),
                           create_option(
                               name="reason",
                               description="Give a reason on why the event is cancelled",
                               option_type=SlashCommandOptionType.STRING,
                               required=False
                           )
                       ])
    @BaseCogs.moderator_restricted
    async def event_cancel(self, ctx: SlashContext, event_id: int, reason: str = None):
        await ctx.send("This command is not yet implemented", hidden=True)

    # Callbacks

    @tasks.loop(minutes=10)
    async def event_loop(self):
        """
        This is the main event loop. This loop will register all the Events to the asynchronism event system
        that are due in less than 30 minutes.
        """
        await self.bot.wait_until_ready()
        current_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)
        delta_timestamp = current_timestamp + timedelta(minutes=15)
        events_to_start = Event.select().where(Event.start_time > current_timestamp,
                                               Event.start_time < delta_timestamp)
        for event in events_to_start:
            self.start_event(event)

        if self.active_event is None:
            event_datetime = datetime.utcnow()
            event_datetime = event_datetime + timedelta(minutes=min(840, max(int(random.gauss(480, 100)), 120)))
            event_duration = min(10, max(int(random.gauss(30, 10)), 50))
            event_model, reward_model = generate_event(duration=event_duration,
                                                       start_time=event_datetime)
            self.active_event = event_model

        # On annule aussi les concours non lancé du passé...
        events_to_cancel = Event.select().where(Event.start_time < current_timestamp,
                                                Event.status == 0)
        for event in events_to_cancel:
            event.status = 3
            event.save()

    @event
    async def giveaway_event(self, event: Event):
        # Les réactions
        actions_line = ViewReactionsLine()
        actions_line.add_reaction(Reaction(button=constants.PARTICIPATE_BUTTON, callback=self.participate_to))
        # Le renderer
        embed_renderer = GiveawayRender(msg_content="@here, a giveaway has started!")

        # Le mix de tout
        giveaway_view = ViewWithReactions(puppet_bot=self.bot,
                                          elements_to_display=event,
                                          render=embed_renderer,
                                          lines=[actions_line])
        if event.target == -1:  # global
            await announcement_cogs.announce_everywhere(self.bot,
                                                        self.cogs_name,
                                                        giveaway_view)
        else:  # guild focused
            await announcement_cogs.announce_in_guild(self.bot,
                                                      self.cogs_name,
                                                      giveaway_view,
                                                      event.target)

    def start_event(self, event: Event):
        if event.status == 0 or event.status == 3:
            event.status = 1
            coroutine = None
            if event.type == 0:  # giveaway
                coroutine = self.giveaway_event
            if not event.started_by:
                self.active_event = event
            loop_object = Loop(coro=coroutine,
                               minutes=0,
                               seconds=0,
                               reconnect=True,
                               hours=0,
                               loop=None,
                               count=1)
            event.save()
            loop_object.start(loop_object, event)

    async def complete_event(self, event_completed: Event):
        if event_completed.status == 1:
            event_completed.status = 2
            event_completed.save()
        else:
            return

        embed_renderer = EventResultRenderer(msg_content="@here, an event has ended!")

        if event_completed.type in [0]:  # giveaway types event
            # we need pick-up a winner
            participants = list(event_completed.participants)
            participants_number = len(participants)
            number_of_winner = 1
            winners = []
            if len(participants) < number_of_winner:
                number_of_winner = len(participants)
            for _ in range(0, number_of_winner):
                index = random.randrange(0, len(participants))
                winners.append(self.bot.get_user(participants[index].discord_user_id))
                participants.pop(index)

            # We assign the gifties
            for reward in event_completed.rewards:
                for winner in winners:
                    if reward.card_id is not None:  # give card
                        CharactersOwnership.create(discord_user_id=winner.id,
                                                   character_id=reward.card_id)
                        await winner.send(f"You have been given the character "
                                          f"{constants.RARITIES_EMOJI[reward.card_id.rarity]} "
                                          f"** [{constants.RARITIES_LABELS[reward.card_id.rarity]}] "
                                          f"{reward.card_id.name} ** because you won a giveaway.")
                    if reward.money_amount is not None:  # we give money
                        economy_model, model_created = Economy.get_or_create(discord_user_id=winner.id)
                        economy_model.add_amount(reward.money_amount)
                        await winner.send(f"You have been given {reward.money_amount} {constants.COIN_NAME} because "
                                          f"you won a giveaway.")
                    if reward.booster_amount is not None:  # we give booster
                        characters_owned_models, characters_models = card_cogs.distribute_cards_to(
                            receiver_id=winner.id,
                            booster_amount=reward.booster_amount)
                        # Toute la section en dessous doit être déplacer dans card_cogs...
                        # Recap listing
                        page_renderer = CharacterListEmbedRender(msg_content=f"{winner.mention}, you have dropped "
                                                                             f"{5 * reward.booster_amount} characters.",
                                                                 menu_title="Summary of dropped characters")
                        page_view = PageView(puppet_bot=self.bot,
                                             elements_to_display=characters_models,
                                             elements_per_page=10,
                                             render=page_renderer)
                        await page_view.display_menu(winner)

                        # First character displaying
                        actions_line = ViewReactionsLine()
                        actions_line.add_reaction(Reaction(button=constants.SELL_BUTTON,
                                                           callback=card_cogs.sell_card))
                        actions_line.add_reaction(Reaction(button=constants.FAVORITE_BUTTON,
                                                           callback=card_cogs.favorite_card))
                        actions_line.add_reaction(Reaction(button=constants.LOCK_BUTTON,
                                                           callback=card_cogs.lock_card))
                        actions_line.add_reaction(Reaction(button=constants.REPORT_BUTTON,
                                                           callback=card_cogs.report_card))

                        common_users = self.bot.get_common_users(winner)
                        character_renderer = CharactersOwnershipEmbedRender(common_users=common_users)
                        characters_view = PageView(puppet_bot=self.bot,
                                                   elements_to_display=characters_owned_models,
                                                   lines=[actions_line],
                                                   elements_per_page=1,
                                                   render=character_renderer)
                        await characters_view.display_menu(winner.dm_channel)

            # We render the winners
            embed_renderer = GiveawayResultRender(msg_content="@here, a giveaway has ended!",
                                                  winners=winners,
                                                  participants_number=participants_number)

        # On mix tout
        giveaway_view = ViewWithReactions(puppet_bot=self.bot,
                                          render=embed_renderer,
                                          elements_to_display=event_completed)

        if event_completed.target == -1:  # global
            await announcement_cogs.announce_everywhere(self.bot,
                                                        self.cogs_name,
                                                        giveaway_view)
        else:  # guild focused
            await announcement_cogs.announce_in_guild(self.bot,
                                                      self.cogs_name,
                                                      giveaway_view,
                                                      event_completed.target)
        # On supprime au passage tous les participants, car plus besoin
        EventParticipants.delete().where(EventParticipants.event_id == event_completed.id)

        if not event_completed.started_by:
            self.active_event = None

    async def participate_to(self, **t):
        menu = t["menu"]
        user_that_interact = t["user_that_interact"]
        context = t["context"]
        event = menu.elements  # Retrieve the event

        if event.status == 1:
            model_created, was_created = EventParticipants.get_or_create(event_id=event.id,
                                                                         discord_user_id=user_that_interact.id)
            if was_created:
                await context.send("You have been registered as a participant for this event!", hidden=True)
            else:
                await context.send("You are already registered in this event.", hidden=True)
            if event.format == 1:
                await self.complete_event(event)
        else:
            await context.send("The event is already over or it was cancelled.", hidden=True)


def generate_event(duration: int, start_time: datetime, card_id: int = None, booster_amount: int = None,
                   money_amount: int = None, format_event: str = "0", winner_number: int = 1,
                   guild_restriction: int = -1, started_by: int = None) -> typing.Tuple[Event, EventRewards]:
    if winner_number < 1:
        return None, None
    if duration < 0:
        return None, None
    if card_id is None and booster_amount is None and money_amount is None:
        action = random.randrange(0, 3)
        if action == 1:  # card giveaway
            all_characters = Character.select()
            card_id = all_characters[random.randrange(0, len(all_characters))].id
        elif action == 2:  # money giveaway
            money_amount = int(random.gauss(60, 10))
            money_amount = min(120, max(money_amount, 20))
        else:  # booster giveaway
            booster_amount = int(random.gauss(3, 1))
            booster_amount = min(6, max(booster_amount, 1))

    # Event creation
    event_model = Event.create(type=0,
                               target=guild_restriction,
                               duration=duration,
                               start_time=start_time,
                               format=int(format_event),
                               status=0,
                               started_by=started_by)
    # Reward creation
    reward_model = EventRewards.create(event_id=event_model.id,
                                       card_id=card_id,
                                       booster_amount=booster_amount,
                                       money_amount=money_amount)
    return event_model, reward_model
