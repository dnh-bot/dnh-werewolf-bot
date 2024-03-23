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

    async def on_start_game(self, embed_data):
        await self.interface.send_action_text_to_channel(
            "cupid_start_game_text", self.channel_name,
            cmd_usages=commands.get_command_usages_str("ship", player_id="ID", player_id1="ID1", player_id2="ID2"),
            cmd_examples=commands.get_command_examples_str("ship")
        )
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
