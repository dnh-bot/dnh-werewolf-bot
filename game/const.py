from enum import Enum


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class NewMoonEvent(Enum):
    NO_EVENT = 0
    HEADS_OR_TAILS = 1
    TWIN_FLAME = 2
    SOMNAMBULISM = 3
    FULL_MOON_VEGETARIAN = 4

    def __str__(self):
        return self.name.lower()
