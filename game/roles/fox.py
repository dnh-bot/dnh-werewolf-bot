from game.roles.villager import Villager


class Fox(Villager):
    # Fox is a Villager but has different winning condition

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Fox

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
