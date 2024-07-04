from game.roles.villager import Villager


class Hunter(Villager):
    """Hunter is basic Villager with ability to kill anyone on his death (die with him)"""

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.__class__.send_before_voting_text(self.interface, self.channel_name, "hunter")
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)
