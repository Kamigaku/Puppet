from discord import Intents
from discord.flags import flag_value


class PuppetIntents(Intents):

    @flag_value
    def scheduled_events(self):
        """:class:`bool`: Whether guild scheduled related events are enabled.

        This corresponds to the following events:

        - :func:`on_scheduled_event_create` (only for guilds)
        - :func:`on_scheduled_event_update` (only for guilds)
        - :func:`on_scheduled_event_delete` (only for guilds)
        - :func:`on_scheduled_event_user_add` (only for guilds)
        - :func:`on_scheduled_event_user_remove` (only for guilds)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 16
