from datetime import timedelta
from typing import List

from discord import Embed, Colour
from discord.abc import User

from discordClient.helper import constants
from discordClient.model.jointure_tables import EventRewards
from discordClient.views import EmbedRender


class GiveawayRender(EmbedRender):

    def generate_render(self, **t) -> Embed:
        reward: EventRewards = t["data"]
        embed = Embed()

        reward_description = "Unknown description"
        reward_colour = 0x000000

        if reward.card_id is not None:
            reward_description = f"{constants.RARITIES_EMOJI[reward.card_id.rarity]} " \
                                 f"** [{constants.RARITIES_LABELS[reward.card_id.rarity]}] {reward.card_id.name} **\n"
            reward_description += ", ".join(
                [affiliation.affiliation_id.name for affiliation in reward.card_id.affiliated_to])
            #reward_colour = Colour(constants.RARITIES_COLORS[reward.card_id.rarity])
            embed.set_thumbnail(url=reward.card_id.image_link)
        elif reward.booster_amount is not None:
            reward_description = f"{constants.PACKAGE_EMOJI} {reward.booster_amount} booster(s)"
            #reward_colour = 0xFFFF00
        elif reward.money_amount is not None:
            reward_description = f"{constants.SELL_EMOJI} {reward.money_amount} {constants.COIN_NAME}"
            #reward_colour = 0x0000FF

        embed.description = f"__The reward for this giveaway is:__\n\n {reward_description}"
        #embed.colour = reward_colour
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
            reward_colour = Colour(constants.RARITIES_COLORS[reward.card_id.rarity])
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
        #embed.timestamp = event.start_time + timedelta(minutes=event.duration)
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
