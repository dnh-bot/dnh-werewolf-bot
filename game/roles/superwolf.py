from game.roles.werewolf import Werewolf


class Superwolf(Werewolf):
    # Superwolf is Werewolf but if check by Seer, will be reported as Villager

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
