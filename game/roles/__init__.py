from game.roles.guard import Guard
from game.roles.seer import Seer
from game.roles.villager import Villager
from game.roles.werewolf import Werewolf
from game.roles.lycan import Lycan
from game.roles.minion import Minion


def get_role_type(cls, name):
    for role in (Villager, Werewolf, Seer, Guard, Lycan, Minion):
        if role.__name__ == name:
            return role

