import logging
import typing
from datetime import datetime, timedelta, timezone
import random
from urllib import request

from discord.ui import Button

from discord import GuildEvent, GuildEventStatus

import discord
from discord import utils
from discord.ext import commands, tasks
from discord.ext.commands import slash_command, InteractionContext, ApplicationCommandField
from discord.ext.tasks import Loop

from discordClient.cogs import card_cogs, announcement_cogs
from discordClient.cogs.abstract import BaseCogs
from discordClient.helper import constants
from discordClient.model import Character, Economy, Settings
from discordClient.model.event import Event
from discordClient.model.jointure_tables import EventRewards, CharactersOwnership
from discordClient.views import CharacterListEmbedRender, SellButton, FavoriteButton, LockButton, ReportButton, \
    CharactersOwnershipEmbedRender
from discordClient.views.view import PageView
from discordClient.views.giveaway_renders import GiveawayResultRender, GiveawayRender
from discordClient.views.view import ViewWithHiddenData


class EventCogs(BaseCogs):

    def __init__(self, bot):
        super().__init__(bot, "event")
        self.next_events: typing.Dict = {}
        self.event_loop.start()

    # Slash commands

    @slash_command(name="giveaway",
                   description="Start a giveaway event",
                   is_global=True)
    @BaseCogs.moderator_restricted
    async def giveaway(self, ctx: InteractionContext,
                       duration: int = ApplicationCommandField(description="Specify the duration, in minutes, of the "
                                                                           "event",
                                                               required=True),
                       card_id: int = ApplicationCommandField(description="Specify the card id that will be dropped"),
                       booster_amount: int = ApplicationCommandField(description="Specify the amount of booster will "
                                                                                 "be given"),
                       money_amount: int = ApplicationCommandField(description="Specify the amount of money that "
                                                                               "will be given"),
                       format: str = ApplicationCommandField(description="Specify the format of the giveaway",
                                                             default_value="0",
                                                             values={"Random": "0",
                                                                     "First": "1"}),
                       winner_number: int = ApplicationCommandField(description="Specify the amount of player that "
                                                                                "will win",
                                                                    default_value=1)):
        await ctx.defer(ephemeral=True)
        if winner_number < 1:
            await ctx.send(content="You need at least 1 winner for the event.",
                           ephemeral=True)
            return
        if duration < 0:
            await ctx.send(content="The minutes you have entered is invalid. It should be a positive integer.",
                           ephemeral=True)
            return
        end_time = datetime.utcnow() + timedelta(minutes=duration)
        event_model, reward_model = generate_event_in_database(end_time=end_time,
                                                               guild_id=ctx.guild.id,
                                                               format_event=format,
                                                               card_id=card_id,
                                                               booster_amount=booster_amount,
                                                               money_amount=money_amount,
                                                               winner_number=winner_number)
        await ctx.send(content="A giveaway event has been created.")
        await self.start_event(context=ctx,
                               event=event_model,
                               event_reward=reward_model)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(self, data: GuildEvent):
        model_event: Event = Event.get_or_none(Event.event_id == data.id)
        if model_event is not None:
            model_event.status = 4
            model_event.save()

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(self, data: GuildEvent):
        model_event: Event = Event.get_or_none(Event.event_id == data.id)
        if model_event is not None:
            model_event.status = data.status.value
            model_event.save()
            if data.status == GuildEventStatus.completed:
                # distribute rewards
                if model_event.type in [0]:  # giveaway types event
                    # we need pick-up a winner
                    participants: list = await data.get_all_users()
                    participants_number: int = len(participants)
                    number_of_winners: int = model_event.number_of_winner
                    winners: list = []
                    if participants_number < number_of_winners:
                        number_of_winners = participants_number
                    for _ in range(0, number_of_winners):
                        index = random.randrange(0, len(participants))
                        winners.append(participants[index])
                        participants.pop(index)

                    # We assign the gifties
                    for reward in model_event.rewards:
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
                                await winner.send(f"You have been given {reward.money_amount} {constants.COIN_NAME} "
                                                  f"because you won a giveaway.")
                            if reward.booster_amount is not None:  # we give booster
                                characters_owned_models, characters_models = card_cogs.distribute_cards_to(
                                    receiver_id=winner.id,
                                    booster_amount=reward.booster_amount)

                                # Recap listing
                                page_renderer = CharacterListEmbedRender(
                                    msg_content=f"{winner.mention}, you have dropped "
                                                f"{5 * reward.booster_amount} characters.",
                                    menu_title="Summary of dropped characters",
                                    owner=winner)
                                page_view = PageView(puppet_bot=self.bot,
                                                     elements_to_display=characters_models,
                                                     elements_per_page=10,
                                                     render=page_renderer)
                                await page_view.display_view(messageable=winner)

                                # First character displaying
                                sell_button: Button = SellButton(row=2)
                                favorite_button: Button = FavoriteButton(row=2)
                                lock_button: Button = LockButton(row=2)
                                report_button: Button = ReportButton(row=2)

                                common_users = self.bot.get_common_users(winner)
                                character_renderer = CharactersOwnershipEmbedRender(common_users=common_users)
                                characters_view = PageView(puppet_bot=self.bot,
                                                           elements_to_display=characters_owned_models,
                                                           elements_per_page=1,
                                                           render=character_renderer)
                                characters_view.add_items([sell_button, favorite_button, lock_button, report_button])
                                await characters_view.display_view(messageable=winner.dm_channel,
                                                                   send_has_reply=False)

                    # We render the winners
                    embed_renderer = GiveawayResultRender(msg_content="@here, a giveaway has ended!",
                                                          winners=winners,
                                                          participants_number=participants_number)
                    winner_view: ViewWithHiddenData = ViewWithHiddenData(puppet_bot=self.bot,
                                                                         elements_to_display=model_event,
                                                                         render=embed_renderer)
                    await announcement_cogs.announce_in_guild(bot=self.bot,
                                                              cogs_name=self.cogs_name,
                                                              view=winner_view,
                                                              guild_id=data.guild_id)

    # Callbacks

    @tasks.loop(minutes=10)
    async def event_loop(self):
        """
        This is the main event loop. This loop will register all the Events to the asynchronism event system
        that are due in less than 30 minutes.
        """
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            # Aucun prochain event de planifier, on vient en planifier un
            if guild.id not in self.next_events or self.next_events[guild.id] is None:
                self.next_events[guild.id] = timedelta(minutes=min(840, max(int(random.gauss(480, 100)), 120)))
                self.bot.logger.debug(f"A event is planned for {guild.id}. "
                                      f"It will be run in {self.next_events[guild.id]}")

            latest_event: Event | None = (Event.select()
                                               .where(Event.status == 2 and Event.guild_id == guild.id)
                                               .order_by(Event.event_id.desc())
                                               .limit(1).get_or_none())
            # On démarre le nouvel event
            if latest_event is None or latest_event.end_time + self.next_events[guild.id] < datetime.utcnow():
                self.bot.logger.debug(f"We are starting the event")
                settings = (Settings.select()
                                    .where(Settings.cog == self.cogs_name and Settings.guild_id == guild.id)
                                    .get_or_none())
                if settings is not None:
                    end_time: datetime = (datetime.utcnow() +
                                          timedelta(minutes=min(10, max(int(random.gauss(30, 10)), 50))))
                    event_model, reward_model = generate_event_in_database(end_time=end_time,
                                                                           guild_id=guild.id)
                    await self.start_event(context=guild.get_channel(settings.channel_id_restriction),
                                           event=event_model,
                                           event_reward=reward_model)
                    self.next_events[guild.id] = None

    @staticmethod
    async def start_event(context: InteractionContext,
                          event: Event,
                          event_reward: EventRewards):
        event_name: str = ""
        event_banner: str | None = None
        event_description: str = ""
        event_location: str = f"{event.number_of_winner} "
        event_location += "winner" if event.number_of_winner == 1 else "winners"
        if event_reward.card_id is not None:  # card rewards
            event_name = f"Card"
            character: Character = Character.get(Character.id == event_reward.card_id)
            event_banner = utils._bytes_to_base64_data(request.urlopen(character.image_link).read())
            event_description = f"{constants.RARITIES_EMOJI[event_reward.card_id.rarity]} "
            event_description += f"** [{constants.RARITIES_LABELS[event_reward.card_id.rarity]}] "
            event_description += f"{event_reward.card_id.name} **\n"
            event_description += ", ".join(
                [affiliation.affiliation_id.name for affiliation in event_reward.card_id.affiliated_to])
        elif event_reward.booster_amount is not None:  # booster rewards
            event_name = "Booster"
            event_description = f"{constants.PACKAGE_EMOJI} {event_reward.booster_amount} booster(s)"
        elif event_reward.money_amount is not None:  # money rewards
            event_name = "Money"
            event_description = f"{constants.SELL_EMOJI} {event_reward.money_amount} {constants.COIN_NAME}"

        if event.format == 0:  # raffle
            event_name = f"{constants.GIFT_EMOJI} {event_name} raffle giveaway {constants.GIFT_EMOJI}"
        elif event.format == 1:  # race
            event_name = f"{constants.GIFT_EMOJI} {event_name} claim giveaway {constants.GIFT_EMOJI}"
        elif event.format == 2:  # bid
            event_name = f"{constants.GIFT_EMOJI} {event_name} bidding giveaway {constants.GIFT_EMOJI}"

        guild_event: GuildEvent = await context.guild.create_external_event(name=event_name,
                                                                            scheduled_start_time=event.end_time,
                                                                            scheduled_end_time=event.end_time +
                                                                                               timedelta(seconds=1),
                                                                            location=event_location,
                                                                            description=event_description,
                                                                            image=event_banner)
        event_link: str = await guild_event.create_link()

        await context.send(content=f"@here A giveaway has started!\r\n{event_link}")

        event.event_id = guild_event.id
        event.save()


def generate_event_in_database(end_time: datetime,
                               guild_id: int,
                               card_id: int = None,
                               booster_amount: int = None,
                               money_amount: int = None,
                               format_event: str = "0",
                               winner_number: int = 1) -> typing.Tuple[Event, EventRewards]:
    if winner_number < 1:
        return None, None
    if card_id is None and booster_amount is None and money_amount is None:
        action = random.randrange(0, 3)
        if action == 0:  # card giveaway
            all_characters = Character.select()
            card_id = all_characters[random.randrange(0, len(all_characters))].id
        elif action == 1:  # money giveaway
            money_amount = int(random.gauss(60, 10))
            money_amount = min(120, max(money_amount, 20))
        else:  # booster giveaway
            booster_amount = int(random.gauss(3, 1))
            booster_amount = min(6, max(booster_amount, 1))

    # Event creation
    event_model = Event.create(guild_id=guild_id,
                               type=0,
                               end_time=end_time,
                               format=int(format_event),
                               number_of_winner=winner_number,
                               status=0)
    # Reward creation
    reward_model = EventRewards.create(event_id=event_model.id,
                                       card_id=card_id,
                                       booster_amount=booster_amount,
                                       money_amount=money_amount)
    return event_model, reward_model


def setup(bot):
    bot.add_cog(EventCogs(bot))
