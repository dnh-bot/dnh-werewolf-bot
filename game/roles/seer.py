from game.roles.villager import Villager


class Seer(Villager):
    """Seer can check 1 person each night to see if they are villager/werewolf"""

    async def on_night(self):
        pass

    async def on_day(self):
        self.target = None

    async def on_action(self, alive_embed_data, *_):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("seer_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)
