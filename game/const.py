from enum import Enum


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class StatusChangeReason(int, Enum):
    def get_template_label(self, game_phase):
        pass

    def is_couple_following(self):
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class DeadReason(StatusChangeReason):
    HIDDEN = -1
    TANNER_NO_VOTE = -2
    LYNCHED = -3
    HUNTED = -4
    SLEPT_OVER = -5
    COUPLE = -6

    def is_couple_following(self):
        return self == self.__class__.COUPLE

    def get_template_label(self, game_phase):
        if self == DeadReason.TANNER_NO_VOTE:
            return "tanner_killed_by_not_voting_text"

        if self == DeadReason.LYNCHED:
            return "execution_player_text"

        if self == DeadReason.HUNTED:
            return "hunter_killed_text"

        if self == DeadReason.SLEPT_OVER:
            return "harlot_died_by_slept_over_text"

        if self == DeadReason.COUPLE:
            return f"couple_died_on_{game_phase.name.lower()}_text"

        return "killed_users_text"


class RebornReason(StatusChangeReason):
    HIDDEN = 1
    COUPLE = 2

    def is_couple_following(self):
        return self == self.__class__.COUPLE

    def get_template_label(self, game_phase):
        if self == RebornReason.COUPLE:
            return "couple_reborn_text"

        return "after_reborn_text"
