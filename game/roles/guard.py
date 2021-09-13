from game.roles.villager import Villager


class Guard(Villager):
    # Guard is basic Villager with ability to protect one person each night
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.yesterday_target = 0

    async def on_night(self):
        # Regain mana
        self.mana = 1

    async def on_day(self):
        if self.mana != 0:  # Guard didn't use skill yesterday.
            self.yesterday_target = 0


    async def on_action(self, embed_data):
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)


    def is_yesterday_target(self, target_id):
        if self.yesterday_target:  # Yesterday player id should not 0
            if self.yesterday_target == target_id:
                return True
            else:
                return False
        else:
            return False


    def set_guard_target(self, target_id):
        self.yesterday_target = target_id