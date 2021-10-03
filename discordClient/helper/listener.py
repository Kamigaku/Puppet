from discord import User, Message

from discordClient.helper import Disposable


class ReactionListener:

    def __init__(self, callback, message: Message, interaction_id: str,
                 bound_to: User = None):
        self.callback = callback
        self.message = message
        if bound_to is not None:
            self.bound_to = bound_to.id
        else:
            self.bound_to = None
        self.interaction_id = interaction_id


class DeleteListener:

    def __init__(self, message: Message, disposable_object: Disposable):
        self.message = message
        self.disposable_object = disposable_object

    def dispose(self):
        self.disposable_object.dispose()
