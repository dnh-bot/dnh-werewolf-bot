from game.roles.character import Character, CharacterStatus


class Villager(Character):

    def on_day(self):
        # if self.status == CharacterStatus.ALIVE:
        #     client.unmute(self.player)  # unmute Village on day for discussion
        pass
        # poll_result = self.vote() ???

    def on_night(self):
        # client.mute(self.player)  # mute Village on night
        pass
