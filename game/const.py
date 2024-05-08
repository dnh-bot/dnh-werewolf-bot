from enum import Enum, auto


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class DeadReason(int, Enum):
    HIDDEN = 0
    TANNER_NO_VOTE = auto()
    LYNCHED = auto()
    HUNTED = auto()
    COUPLE = auto()

    def get_label(self, game_phase):
        if self == DeadReason.TANNER_NO_VOTE:
            return "tanner_killed_by_not_voting_text"

        if self == DeadReason.LYNCHED:
            return "execution_player_text"

        if self == DeadReason.HUNTED:
            return "hunter_killed_text"

        if self == DeadReason.COUPLE:
            return f"couple_died_on_{game_phase.name.lower()}_text"

        return "killed_users_text"

    def __str__(self):
        return self.name.lower()
