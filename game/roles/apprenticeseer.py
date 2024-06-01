from game.roles.seer import Seer
import text_templates


class ApprenticeSeer(Seer):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.is_active = False

    def register_target(self, target_id):
        if not self.is_active:
            return text_templates.generate_text("invalid_apprenticeseer_text")
        return super().register_target(target_id)

    async def on_night(self):
        pass

    async def on_day(self):
        self.target = None

    async def set_active(self, active):
        if self.is_alive() and active != self.is_active:
            if active:
                await self.interface.send_action_text_to_channel("apprenticeseer_announce_text", self.channel_name)
            else:
                await self.interface.send_action_text_to_channel("apprenticeseer_learn_text", self.channel_name)
        self.is_active = active

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            if self.is_active:
                await self.interface.send_action_text_to_channel("seer_before_voting_text", self.channel_name)
                await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)
            else:
                await self.interface.send_action_text_to_channel("apprenticeseer_learn_text", self.channel_name)
