import text_templates
from game.roles.villager import Villager


class Pathologist(Villager):
    """Pathologist can check 1 dead person each night to see their's role"""

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)

    async def on_night(self):
        pass


    async def on_night_start(self, _, dead_embed_data):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("pathologist_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(dead_embed_data, self.channel_name)
