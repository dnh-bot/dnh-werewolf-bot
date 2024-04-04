import text_templates
from game.roles.villager import Villager


class Guard(Villager):
    allow_self_protection = False

    # Guard is basic Villager with ability to protect one person each night
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.yesterday_target = None

    @staticmethod
    def set_allow_self_protection(allow_self_protection):
        Guard.allow_self_protection = allow_self_protection

    async def on_night(self):
        pass

    async def on_day(self):
        self.yesterday_target = self.target
        self.target = None

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("guard_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)

    def is_yesterday_target(self, target_id):
        return self.yesterday_target == target_id

    def generate_invalid_target_text(self, target_id):
        if not Guard.allow_self_protection and self.player_id == target_id:
            return text_templates.generate_text("invalid_guard_selfprotection_text")
        if self.is_yesterday_target(target_id):
            return text_templates.generate_text("invalid_guard_yesterdaytarget_text")

        return ""
