from game.roles.villager import Villager


class Diseased(Villager):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Villager
