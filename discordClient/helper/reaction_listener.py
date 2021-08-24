class ReactionListener:

    def __init__(self, event_type: str, emoji, callback, puppet_id: int = -1, remove_reaction: bool = False,
                 return_emoji: bool = False):
        if type(event_type) is not list:
            self.event_type = [event_type]
        else:
            self.event_type = event_type
        self.return_emoji = return_emoji
        if type(emoji) is not list:
            self.emoji = [emoji]
        else:
            self.emoji = emoji
        self.callback = callback
        self.puppet_id = puppet_id
        self.remove_reaction = remove_reaction
