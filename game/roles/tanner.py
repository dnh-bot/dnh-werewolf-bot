from game.roles.villager import Villager


class Tanner(Villager):
    # Tanner is Tanner party, wins game by voted out during dayphase

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
