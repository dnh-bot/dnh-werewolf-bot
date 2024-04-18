from game.roles.villager import Villager


class Tanner(Villager):
    # Tanner is Tanner party, wins game by voted out during dayphase

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Tanner

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
