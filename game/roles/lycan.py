from game.roles.villager import Villager


class Lycan(Villager):
    # Lycan is a Villager but if checked by the Seer, will be reported as Werewolf

    @classmethod
    def get_character_description(cls):
        return "Lycan. Vẫn là một Villager nhưng bị Seer soi ra là Werewolf."

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return True
