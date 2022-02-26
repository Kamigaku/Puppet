import abc
import typing

from peewee import fn

import discord

from discordClient.helper import constants
from discordClient.model import CharactersOwnership, CharacterFavorites, Character, Affiliation, CharacterAffiliation


class CallableButton(discord.ui.Button):

    def __init__(self, callback_method: typing.Callable = None, **kwargs):
        super().__init__(**kwargs)
        self.callback_method = callback_method

    async def callback(self, interaction: discord.Interaction):
        if self.callback_method is not None:
            await self.callback_method(self, interaction)


class SellButton(discord.ui.Button):

    def __init__(self, row: int, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.green,
                         label="Sell",
                         emoji=constants.SELL_EMOJI,
                         disabled=disabled,
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        user_that_interact = interaction.user
        ownership_model = self.view.retrieve_element(self.view.page)
        if user_that_interact.id == ownership_model.discord_user_id:
            price_sold = ownership_model.sell()
            if price_sold > 0:
                await user_that_interact.send(f"You have sold this card for {price_sold} {constants.COIN_NAME}.")
                await interaction.response.defer(ephemeral=True)
            else:
                await interaction.response.send_message(content=f"You have already sold this card and cannot sell it "
                                                                f"again. If you think this is an error, please "
                                                                f"communicate to a moderator.",
                                                        ephemeral=True)
        else:
            await interaction.response.send_message(content="You are not the owner of the card, you cannot sell it.",
                                                    ephemeral=True)


class ReportButton(discord.ui.Button):

    def __init__(self, row: int, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.red,
                         label="Report",
                         emoji=constants.REPORT_EMOJI,
                         disabled=disabled,
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        character_id = self.view.retrieve_element(self.view.page).character_id
        character = Character.get_by_id(character_id)
        embed = discord.Embed()
        embed.title = f"{constants.REPORT_EMOJI} Report a card"
        embed.colour = 0xFF0000
        embed.description = f"Hello, you are on your way to report the card **{character.name}**.\n\n"
        embed.description += "Reporting a card means that the current card has something that you judge " \
                             "incoherent, invalid or maybe because the card should not exist.\n\n **__Please " \
                             "note that your report will be sent to a moderator that will review them in " \
                             "order to judge if they are valid or not. Do not add any personal datas or " \
                             "anything that could lead to a ban of the Puppet project.__**\n\n To be more " \
                             "precise on the category of your report, you will find below a list of commands " \
                             "that you can send to describe the type of report you want to do : "
        embed.set_thumbnail(url=character.image_link)
        embed.add_field(name="__Description incoherency__",
                        value=f"/report description {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid image__",
                        value=f"/report image {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid affiliation(s)__",
                        value=f"/report affiliation {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Invalid name__",
                        value=f"/report name {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Card incoherency__",
                        value=f"/report card {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        embed.add_field(name="__Other report__",
                        value=f"/report other {character_id} **\"[YOUR COMMENT]\"**",
                        inline=False)
        await interaction.user.send(embed=embed)
        await interaction.response.defer(ephemeral=True)


class LockButton(discord.ui.Button):

    def __init__(self, row: int, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Lock",
                         emoji=constants.LOCK_EMOJI,
                         disabled=disabled,
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        ownership_model = self.view.retrieve_element(self.view.page)
        if interaction.user.id == ownership_model.discord_user_id:
            new_state = ownership_model.lock()
            if new_state:
                await interaction.response.send_message(content=f"You have locked the card {ownership_model}.",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(content=f"You have unlocked the card {ownership_model}.",
                                                        ephemeral=True)
        else:
            await interaction.response.send_message(content="You are not the owner of the card, you cannot lock it.",
                                                    ephemeral=True)


class FavoriteButton(discord.ui.Button):

    def __init__(self, row: int, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Favorite",
                         emoji=constants.HEART_EMOJI,
                         disabled=disabled,
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        user_that_interact = interaction.user
        character_model = self.view.retrieve_element(self.view.page)
        if type(character_model) is CharactersOwnership:
            character_model = character_model.character_id
        model, model_created = CharacterFavorites.get_or_create(character_id=character_model.id,
                                                                discord_user_id=user_that_interact.id)
        if not model_created:
            model.delete_instance()
        if model_created:
            await interaction.response.send_message(content=f"You added to your favorites the card {character_model}.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(content=f"You removed from your favorites the card {character_model}.",
                                                    ephemeral=True)


class ValidateTradeButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.green,
                         label="Validate",
                         emoji=constants.CHECK_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class CancelTradeButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.red,
                         label="Cancel",
                         emoji=constants.RED_CROSS_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class ChangeOwnerButton(discord.ui.Button):

    def __init__(self, row: int, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Change owner",
                         emoji=constants.ROTATE_EMOJI,
                         disabled=disabled,
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        trade_data = self.view.get_hidden_data()
        if trade_data.current_user == trade_data.origin:
            trade_data.current_user = trade_data.destination
        else:
            trade_data.current_user = trade_data.origin

        query, elements_to_display = ChangeOwnerButton._generate_request(trade_data.current_user.id)
        trade_data.request = query

        self.view.render.change_owner(trade_data.current_user)
        self.view.update_datas(elements_to_display=query)
        await self.view.update_view()

    @staticmethod
    def _generate_request(user_id, rarity: typing.List[int] = None, affiliation: str = None):
        query = (CharactersOwnership.select(CharactersOwnership.id, CharactersOwnership.discord_user_id,
                                            Character.name, Character.category, Character.rarity, Character.id,
                                            fn.GROUP_CONCAT(Affiliation.name, ", ").alias("affiliations"))
                 .join_from(CharactersOwnership, Character)
                 .join_from(Character, CharacterAffiliation)
                 .join_from(CharacterAffiliation, Affiliation))

        if rarity is not None:
            query = query.where(Character.rarity << rarity)
        if affiliation is not None:
            query = (query.where(Affiliation.name == affiliation))

        query = (query.where((CharactersOwnership.discord_user_id == user_id) &
                             (CharactersOwnership.is_sold == False) &
                             (CharactersOwnership.is_locked == False))
                 .group_by(CharactersOwnership.id)
                 .order_by(Character.rarity.desc(), Character.name.asc()))

        elements_to_display = []
        for ownership in query:
            character = ownership.character_id
            affiliation_text = ownership.affiliations
            character_field = f"{constants.RARITIES_EMOJI[character.rarity]} " \
                              f"**[{constants.RARITIES_LABELS[character.rarity]}] {character.name}**"
            character_field += f"\n{affiliation_text}\n"
            elements_to_display.append(character_field)
        return query, elements_to_display


class LockFilterButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Display locked",
                         emoji=constants.LOCK_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class UnlockFilterButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Display unlocked",
                         emoji=constants.UNLOCK_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class FavoritedFilterButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Display favorited",
                         emoji=constants.HEART_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class NonFavoritedFilterButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label="Display non-favorited",
                         emoji=constants.BROKEN_HEART_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)


class RemoveFilterButton(CallableButton):

    def __init__(self,
                 row: int,
                 disabled: bool = False,
                 callback_method: typing.Callable = None):
        super().__init__(style=discord.ButtonStyle.red,
                         label="Remove filters",
                         emoji=constants.RED_CROSS_EMOJI,
                         disabled=disabled,
                         row=row,
                         callback_method=callback_method)
