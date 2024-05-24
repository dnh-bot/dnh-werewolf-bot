import text_templates
from game.roles.villager import Villager


class Pathologist(Villager):
    """Pathologist can check 1 dead person each night to see their's role"""

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.autopsy_target = None

    async def on_night(self):
        pass


    async def on_night_start(self, _, dead_embed_data):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("pathologist_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(dead_embed_data, self.channel_name)

    def get_autopsy_target(self):
        return self.autopsy_target

    def set_autopsy_target(self, target_id):
        self.autopsy_target = target_id

    def register_autopsy_target(self, target_id):

        self.set_autopsy_target(target_id)

        return text_templates.generate_text("pathologist_after_voting_text", target=f"<@{target_id}>") \
            + text_templates.generate_text("inform_power_used_text")