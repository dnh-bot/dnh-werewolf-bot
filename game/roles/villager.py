from game.roles.character import Character, CharacterStatus


class Villager(Character):
    def on_day(self):
        # poll_result = self.vote()
        pass

    def on_night(self):
        # client.mute(self.player)  # mute Village on night
        pass
