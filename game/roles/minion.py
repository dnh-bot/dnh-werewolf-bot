from game.roles.werewolf import Werewolf


class Minion(Werewolf):
    # Minion is Werewolf but if check by Seer, will be reported as Villageri

    async def on_night(self):
        # poll_result = self.vote()
        pass

    def is_werewolf(self):
        return False
