import text_templates
from game.roles.villager import Villager


class Hunter(Villager):
    """Hunter is basic Villager with ability to kill anyone on his death (die with him)"""

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.target = None

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("hunter_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)

    def get_target(self):
        return self.target

    def set_target(self, target_id):
        self.target = target_id

    def is_valid_target(self, target_id):
        return target_id is not None and target_id != self.player_id

    def register_target(self, target):
        target_id = target.player_id
        if self.is_valid_target(target_id):
            self.set_target(target_id)
        else:
            self.set_target(None)

        return text_templates.generate_text("hunter_after_voting_text", target=f"<@{target_id}>")
