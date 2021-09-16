from discord import User, Message

from discordClient.helper.disposable import Disposable


class ReactionListener:

    def __init__(self, event_type, emoji, callback, message: Message, bound_to: User = None,
                 remove_reaction: bool = False, return_emoji: bool = False):
        if type(event_type) is not list:
            self.event_type = [event_type]
        else:
            self.event_type = event_type
        if type(emoji) is not list:
            self.emoji = [emoji]
        else:
            self.emoji = emoji
        self.callback = callback
        self.message = message
        if bound_to is not None:
            self.bound_to = bound_to.id
        else:
            self.bound_to = None
        self.remove_reaction = remove_reaction
        self.return_emoji = return_emoji


class DeleteListener:

    def __init__(self, message: Message, disposable_object: Disposable):
        self.message = message
        self.disposable_object = disposable_object

    def dispose(self):
        self.disposable_object.dispose()
