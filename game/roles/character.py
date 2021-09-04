from enum import Enum


class CharacterStatus(Enum):
    ALIVE = 1
    KILLED = 2
    PROTECTED = 3


class Character:
    def __init__(self, player_id):
        self.player_id = player_id
        self.status = CharacterStatus.ALIVE

    def is_alive(self):
        return self.status == CharacterStatus.ALIVE

    def get_killed(self):
        self.status = CharacterStatus.KILLED

    def action(self):
        pass

    def on_phase(self, phase):
        # if phase == game.GamePhase.DAY:
        #     self.on_day()
        # elif phase == game.GamePhase.NIGHT:
        #     self.on_night()
        pass

    def on_day(self):
        pass

    def on_night(self):
        pass

    def vote(self):
        pass
