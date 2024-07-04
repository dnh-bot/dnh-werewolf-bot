import commands
from game.roles.villager import Villager


class Cupid(Villager):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.power = 1

    def get_power(self):
        return self.power

    def on_use_power(self):
        self.power = 0

    async def on_start_game(self, embed_data, _):
        await self.__class__.send_before_voting_text(self.interface, self.channel_name, "ship")
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
