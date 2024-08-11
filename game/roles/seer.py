from game.roles.villager import Villager


class Seer(Villager):
    """Seer can check 1 person each night to see if they are villager/werewolf"""

    can_kill_fox = True

    @staticmethod
    def set_can_kill_fox(can_kill_fox):
        Seer.can_kill_fox = can_kill_fox

    @staticmethod
    def is_can_kill_fox():
        return Seer.can_kill_fox

    async def on_night(self):
        pass

    async def on_day(self):
        self.target = None

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("seer_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)
