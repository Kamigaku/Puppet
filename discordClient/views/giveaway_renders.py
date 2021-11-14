import datetime
import math
from datetime import timedelta, timezone
from typing import List

from discord import Embed
from discord.abc import User

from discordClient.helper import constants
from discordClient.views import EmbedRender


class GiveawayRender(EmbedRender):

    def generate_render(self, **t) -> Embed:
        event = t["data"]
        reward = event.rewards[0]
        embed = Embed()
        end_timestamp = math.floor((event.start_time.replace(tzinfo=timezone.utc) +
                                    timedelta(minutes=event.duration)).timestamp())

        if reward.card_id is not None:
            reward_description = f"{constants.RARITIES_EMOJI[reward.card_id.rarity]} " \
                                 f"** [{constants.RARITIES_LABELS[reward.card_id.rarity]}] {reward.card_id.name} **\n"
            reward_description += ", ".join(
                [affiliation.affiliation_id.name for affiliation in reward.card_id.affiliated_to])
            reward_header = "Card"
            reward_colour = constants.RARITIES_COLORS[reward.card_id.rarity]
            embed.set_thumbnail(url=event.rewards[0].card_id.image_link)
        elif reward.booster_amount is not None:
            reward_description = f"{constants.PACKAGE_EMOJI} {reward.booster_amount} booster(s)"
            reward_header = "Booster"
            reward_colour = 0xFFFF00
        elif reward.money_amount is not None:
            reward_description = f"{constants.SELL_EMOJI} {reward.money_amount} {constants.COIN_NAME}"
            reward_header = "Money"
            reward_colour = 0x0000FF

        if event.format == 0:  # raffle
            embed.set_author(name=f"{constants.GIFT_EMOJI} {reward_header} raffle giveaway {constants.GIFT_EMOJI}")
        elif event.format == 1:  # race
            embed.set_author(name=f"{constants.GIFT_EMOJI} {reward_header} claim giveaway {constants.GIFT_EMOJI}")
        elif event.format == 2:  # bid
            embed.set_author(name=f"{constants.GIFT_EMOJI} {reward_header} bidding giveaway {constants.GIFT_EMOJI}")
        description = f"A giveaway has started !\n\n"
        if event.format == 1:
            description += f"**Will ends <t:{end_timestamp}:R> if no one claims the price\n**"
        else:
            description += f"**Ends <t:{end_timestamp}:R>\n**"
        description += "__The reward for this giveaway is:__\n\n"
        description += reward_description
        description += "\n\nPress the button below to participate!"
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = description
        embed.colour = reward_colour
        return embed


class GiveawayResultRender(EmbedRender):

    def __init__(self, msg_content: str, winners: List[User], participants_number: int):
        super().__init__(msg_content=msg_content)
        self.winners = winners
        self.participants_number = participants_number

    def generate_render(self, **t) -> Embed:
        event = t["data"]
        reward = event.rewards[0]

        embed = Embed()
        reward_colour = 0xFFFFFF
        reward_header = "NOT_IMPLEMENTED"
        if reward.card_id is not None:
            reward_header = "Card"
            reward_colour = constants.RARITIES_COLORS[reward.card_id.rarity]
        elif reward.booster_amount is not None:
            reward_header = "Booster"
            reward_colour = 0xFFFF00
        elif reward.money_amount is not None:
            reward_header = "Money"
            reward_colour = 0x0000FF

        if event.format == 0:  # raffle
            embed.set_author(name=f"{constants.BELL_EMOJI} {reward_header} raffle result {constants.BELL_EMOJI}")
        elif event.format == 1:  # race
            embed.set_author(name=f"{constants.BELL_EMOJI} {reward_header} race result {constants.BELL_EMOJI}")
        elif event.format == 2:  # bid
            embed.set_author(name=f"{constants.BELL_EMOJI} {reward_header} bidding result {constants.BELL_EMOJI}")
        embed.timestamp = event.start_time + timedelta(minutes=event.duration)
        if len(self.winners) > 0:
            description = "A giveaway has ended...\r\n"
            description += f"There was **{self.participants_number} participants**.\r\n"
            description += "The winners are:\r\n"
            for winner in self.winners:
                if winner is not None:
                    description += f"\t- {winner.mention}\r\n"
            description += "\r\n Congratulations, you will receive your price automatically."
        else:
            description = "A giveaway has ended but there was no participant!"
        embed.description = description
        embed.colour = reward_colour
        return embed


class EventResultRenderer(EmbedRender):

    def generate_render(self, **t) -> Embed:
        event = t["data"]
        embed = Embed()
        embed.set_author(name=f"{constants.BELL_EMOJI} Card giveaway {constants.BELL_EMOJI}")
        embed.timestamp = event.start_time
        embed.description = f"A giveaway has ended !\nWinner is not defined for the moment..."
        return embed
