from game.roles.character import Character, CharacterStatus


class Villager(Character):
    @classmethod
    def get_character_description(cls):
        return "Villager - Dân thường. Có thể vote vào ban ngày và đi ngủ vào ban đêm."

    async def on_day(self):
        pass

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
