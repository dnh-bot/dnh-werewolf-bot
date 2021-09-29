from game.roles.villager import Villager


class Fox(Villager):
    # Fox is a Villager but has different winning condition

    @classmethod
    def get_character_description(cls):
        return "Fox - Cáo. Là kẻ ở phe thứ 3. Nếu bị Seer soi thì Fox sẽ chết."

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
