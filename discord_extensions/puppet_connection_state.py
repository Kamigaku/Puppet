from discord.state import ConnectionState


class PuppetConnectionState(ConnectionState):

    def on_guild_scheduled_event_create(self, data):
        pass