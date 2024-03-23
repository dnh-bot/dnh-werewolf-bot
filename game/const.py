from enum import Enum


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class NewMoonEvent(Enum):
    NO_EVENT = "no_event"
    HEADS_OR_TAILS = "heads_or_tails"
    TWIN_FLAME = "twin_flame"
    SOMNAMBULISM = "somnambulism"
    FULL_MOON_VEGETARIAN = "full_moon_vegetarian"
