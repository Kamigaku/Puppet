from discord import Embed
from peewee import *

from discordClient.helper import constants
from discordClient.model import Character
from discordClient.model.meta_model import BaseModel


class Report(BaseModel):
    category = CharField()
    card_id = IntegerField()
    comment = TextField()
    reporter_user_id = IntegerField()
    has_been_treated = BooleanField(default=False)
    action_done = TextField(default="")

    def generate_embed(self) -> Embed:
        character_embed = Character.get_by_id(self.card_id)
        report_embed = Embed()
        report_embed.set_author(name=f"{character_embed.name} - Category: {self.category}")
        report_embed.title = f"{constants.WARNING_EMOJI} Report"
        report_embed.description = self.comment
        report_embed.colour = 0xFF0000
        report_embed.add_field(name="__Report fixing__",
                               value=f"{constants.BOT_PREFIX} report_fix {self.id} \"[YOUR COMMENT]\"")
        report_embed.set_footer(text=f"Character_id: {self.card_id}")
        return report_embed

    def fix(self, action_done: str):
        self.has_been_treated = True
        self.action_done = action_done
        self.save()


