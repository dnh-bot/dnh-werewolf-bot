from game.roles.villager import Villager


class Seer(Villager):
    """Seer can check 1 person each night to see if they are villager/werewolf"""

    async def on_night(self):
        pass

    async def on_day(self):
        self.target = None

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.__class__.send_before_voting_text(self.interface, self.channel_name, "seer")
            await self.interface.send_embed_to_channel(embed_data, self.channel_name)
