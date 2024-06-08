from game.roles.villager import Villager


class Tanner(Villager):
    # Tanner is Tanner party, wins game by voted out during dayphase
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Tanner
        self.is_voted_other = False
        self.is_lynched = False

    async def on_day_start(self, day):
        await super().on_day_start(day)
        if day >= 7:
            self.party = Villager

        self.is_voted_other = False
