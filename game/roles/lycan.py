from game.roles.villager import Villager


class Lycan(Villager):
    # Lycan is a Villager but if checked by the Seer, will be reported as Werewolf

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return True
