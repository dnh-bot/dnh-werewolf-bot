from game.roles.character import Character, CharacterStatus


class Villager(Character):
    async def on_day(self):
        # poll_result = self.vote()
        pass

    async def on_night(self):
        # client.mute(self.player_id)  # mute Village on night
        pass

    def seer_seen_as_werewolf(self):
        return False
