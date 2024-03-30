from game.roles.villager import Villager


class Witch(Villager):
    # Witch can reborn a dead player 1 time in a game

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.power = 1
        self.curse_power = 1
        self.reborn_target = None
        self.curse_target = None

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
