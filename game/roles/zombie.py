from game.roles.villager import Villager


class Zombie(Villager):
    # Zombie can reborn himself 1 time in a game.

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.power = 1

    def get_power(self):
        return self.power

    def on_use_power(self):
        self.power = 0

    async def on_night(self):
        pass

    async def on_action(self, *_):
        if not self.is_alive() and self.get_power():
            await self.interface.send_action_text_to_channel("zombie_before_voting_text", self.channel_name)
