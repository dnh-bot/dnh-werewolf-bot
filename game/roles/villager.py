from game.roles.character import Character


class Villager(Character):
    async def on_day(self):
        pass

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
