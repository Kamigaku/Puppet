from peewee import *

from discordClient.model import CharactersOwnership
from discordClient.model.meta_model import BaseModel


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
            return True
        else:
            return False

    def accept_trade(self) -> bool:
        if self.state == 0:

            applicant_cards = self.applicant_cards.split("-")
            recipient_cards = self.recipient_cards.split("-")

            if applicant_cards and len(applicant_cards) > 0:
                for card in applicant_cards:
                    if card:
                        ownership_model = CharactersOwnership.get_by_id(int(card))
                        ownership_model.trade_to(self.recipient)

            if recipient_cards and len(recipient_cards) > 0:
                for card in recipient_cards:
                    if card:
                        ownership_model = CharactersOwnership.get_by_id(int(card))
                        ownership_model.trade_to(self.applicant)

            self.state = 2
            self.save()
            return True
        else:
            return False
