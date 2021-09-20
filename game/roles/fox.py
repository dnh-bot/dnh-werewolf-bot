from game.roles.villager import Villager


class Fox(Villager):
    # Fox is a Villager but has different winning condition

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
