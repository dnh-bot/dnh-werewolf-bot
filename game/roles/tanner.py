from game.roles.villager import Villager


class Tanner(Villager):
    # Tanner is Tanner party, wins game by voted out during dayphase
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.is_voted = False
        self.final_party = 'Tanner'
        self.is_lynched = False
