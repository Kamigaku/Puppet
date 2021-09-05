from discord import Embed, User
from peewee import *

from discordClient.helper import constants
from discordClient.model.meta_model import BaseModel
import discordClient.model as model


class Trade(BaseModel):
    applicant = IntegerField()
    recipient = IntegerField()
    applicant_cards = TextField(null=False)
    recipient_cards = TextField(null=False)
    state = IntegerField(default=0)

    def refuse_trade(self) -> bool:
        if self.state == 0:
            self.state = 1
            self.save()
        else:
            return False

    def accept_trade(self) -> bool:
        if self.state == 0:

            applicant_cards = self.applicant_cards.split("-")
            recipient_cards = self.recipient_cards.split("-")

            if applicant_cards and len(applicant_cards) > 0:
                for card in applicant_cards:
                    if card:
                        ownership_model = model.CharactersOwnership.get_by_id(int(card))
                        ownership_model.trade_to(self.recipient)

            if recipient_cards and len(recipient_cards) > 0:
                for card in recipient_cards:
                    if card:
                        ownership_model = model.CharactersOwnership.get_by_id(int(card))
                        ownership_model.trade_to(self.applicant)

            self.state = 2
            self.save()
            return True
        else:
            return False

    def generate_embed(self, applicant: User, recipient: User) -> Embed:

        # Cette section est pour moi incohérente mais il est compliqué de faire en sorte que le trade vienne
        # récupérer les infos du créateur de l'offre et du destinataire car ce sont des objets discord
        if applicant.id != self.applicant and recipient.id != self.recipient:
            raise ValueError("The applicant and the recipient are the one used in the trade.")

        applicant_cards = self.applicant_cards.split("-")
        recipient_cards = self.recipient_cards.split("-")

        query_applicant = (model.Character.select(model.Character, model.CharactersOwnership.id.alias("id_own"))
                                          .join(model.CharactersOwnership)
                                          .where(model.CharactersOwnership.id << applicant_cards))
        query_recipient = (model.Character.select(model.Character, model.CharactersOwnership.id.alias("id_own"))
                                          .join(model.CharactersOwnership)
                                          .where(model.CharactersOwnership.id << recipient_cards))

        applicant_chars = []
        for applicant_card in query_applicant:
            applicant_chars.append(f"{applicant_card.charactersownership.id_own} • "
                                   f"{constants.RARITIES_EMOJI[applicant_card.rarity]} "
                                   f"[**{constants.RARITIES_LABELS[applicant_card.rarity]}**] {applicant_card.name}")

        recipient_chars = []
        for recipient_card in query_recipient:
            recipient_chars.append(f"{recipient_card.charactersownership.id_own} • "
                                   f"{constants.RARITIES_EMOJI[recipient_card.rarity]} "
                                   f"[**{constants.RARITIES_LABELS[recipient_card.rarity]}**] {recipient_card.name}")

        embed_trade = Embed()
        embed_trade.title = "Trade recap"
        embed_trade.description = f"This section recap the trade offer between " \
                                  f"**{applicant.name}#{applicant.discriminator}** and " \
                                  f"**{recipient.name}#{recipient.discriminator}**"
        embed_trade.set_author(name=f"{applicant.name}#{applicant.discriminator}", icon_url=applicant.avatar_url)
        embed_trade.set_thumbnail(url=recipient.avatar_url)

        value_applicant = "\n".join(applicant_chars)
        if not value_applicant:
            value_applicant = "None"
        value_recipient = "\n".join(recipient_chars)
        if not value_recipient:
            value_recipient = "None"

        embed_trade.add_field(name=f"{applicant.name}#{applicant.discriminator}", value=value_applicant)
        embed_trade.add_field(name=f"{recipient.name}#{recipient.discriminator}", value=value_recipient)
        embed_trade.set_footer(text=f"Trade_id: {self.id} | Puppet_id: {constants.PUPPET_IDS['TRADE_COGS_OFFER']}")
        return embed_trade
