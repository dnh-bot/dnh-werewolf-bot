from game.roles.werewolf import Werewolf


class Superwolf(Werewolf):
    # Superwolf is Werewolf but if check by Seer, will be reported as Villager

    @classmethod
    def get_character_description(cls):
        return "Superwolf - Sói già: Chọn 1 người để giết mỗi đêm. Sói già có khả năng che giấu Tiên tri và không bị soi ra là sói."

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
