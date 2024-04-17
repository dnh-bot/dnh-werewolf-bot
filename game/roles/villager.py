from game.roles.character import Character


class Villager(Character):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Villager

    async def on_day(self):
        pass

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return False
