from enum import Enum, IntEnum, auto


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class CommandType(IntEnum):
    PUBLIC = 0
    LOBBY = auto()
    GAMEPLAY = auto()
    WEREWOLF = auto()
    PERSONAL = auto()

    def __str__(self):
        return self.name.lower() + " commands"


ChannelType = CommandType
