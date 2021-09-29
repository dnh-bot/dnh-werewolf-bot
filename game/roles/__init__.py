from game.roles.villager import Villager
from game.roles.werewolf import Werewolf
from game.roles.guard import Guard
from game.roles.seer import Seer
from game.roles.lycan import Lycan
from game.roles.superwolf import Superwolf
from game.roles.fox import Fox
from game.roles.witch import Witch
from game.roles.cupid import Cupid


def get_all_roles():
    return (Villager, Werewolf, Seer, Guard, Lycan, Superwolf, Fox, Witch, Cupid)


def get_role_type(name):
    for role in get_all_roles():
        if role.__name__ == name:
            return role
