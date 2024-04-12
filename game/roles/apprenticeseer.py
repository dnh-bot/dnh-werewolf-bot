from game.roles.seer import Seer
import text_templates


class ApprenticeSeer(Seer):
    """ApprenticeSeer can check 1 person each night to see if they are villager/werewolf if the Seer is dead"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.is_active = False


    def register_target(self, target_id):
        if self.is_alive() and self.is_active:
            return super().register_target(target_id)
        return text_templates.generate_text("apprenticeseer_invalid_register_target_text")


    async def set_active(self, active):
        if self.is_alive() and active != self.is_active:
            if active:
                await self.interface.send_action_text_to_channel("apprenticeseer_on_active_text", self.channel_name)
            else:
                await self.interface.send_action_text_to_channel("apprenticeseer_on_inactive_text", self.channel_name)
        self.is_active = active


    async def on_action(self, alive_embed_data, _):
        if self.is_alive() and self.is_active:
            await self.interface.send_action_text_to_channel("apprenticeseer_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)
