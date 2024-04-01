import text_templates
from game.roles.villager import Villager


class Witch(Villager):
    # Witch can reborn a dead player 1 time in a game
    can_kill = True

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.power = 1
        self.curse_power = 1
        self.reborn_target = None
        self.curse_target = None

    @staticmethod
    def set_can_kill(can_kill):
        Witch.can_kill = can_kill

    @staticmethod
    def is_can_kill():
        return Witch.can_kill

    def get_power(self):
        return self.power

    def on_use_power(self):
        self.power = 0

    def get_curse_power(self):
        return self.curse_power

    def on_use_curse_power(self):
        self.curse_power = 0

    async def on_night(self):
        pass

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("witch_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)

    def get_reborn_target(self):
        return self.reborn_target

    def set_reborn_target(self, target_id):
        self.reborn_target = target_id

    def get_curse_target(self):
        return self.curse_target

    def set_curse_target(self, target_id):
        self.curse_target = target_id

    def register_reborn_target(self, target_id):
        if self.get_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        self.set_reborn_target(target_id)

        return text_templates.generate_text("witch_after_reborn_text", target=f"<@{target_id}>")

    def register_curse_target(self, target_id):
        if not Witch.is_can_kill():
            return text_templates.generate_text("invalid_author_text")

        if self.get_curse_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        self.set_curse_target(target_id)

        return text_templates.generate_text("witch_after_curse_text", target=f"<@{target_id}>")
