from game.roles.villager import Villager


class Guard(Villager):
    # Guard is basic Villager with ability to protect one person each night
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.target = None
        self.yesterday_target = None

    async def on_night(self):
        # Regain mana
        self.mana = 1
        self.target = None

    async def on_day(self):
        self.yesterday_target = self.target

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("guard_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)

    def is_yesterday_target(self, target_id):
        return self.yesterday_target == target_id

    def get_target(self):
        return self.target

    def set_target(self, target_id):
        self.target = target_id
