import text_templates
from game.roles.villager import Villager


class Harlot(Villager):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Villager
        self.yesterday_target = None

    async def on_day(self):
        self.yesterday_target = self.target
        self.target = None

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("harlot_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)

    def is_yesterday_target(self, target_id):
        return self.yesterday_target == target_id

    def generate_invalid_target_text(self, target_id):
        if self.is_yesterday_target(target_id):
            return text_templates.generate_text("invalid_harlot_yesterday_target_text")

        return ""
