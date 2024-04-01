from game.roles.villager import Villager


class Hunter(Villager):
    """Hunter is basic Villager with ability to kill anyone on his death (die with him)"""

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("hunter_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
