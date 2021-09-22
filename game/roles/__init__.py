from game.roles.guard import Guard
from game.roles.seer import Seer
from game.roles.villager import Villager
from game.roles.werewolf import Werewolf
from game.roles.lycan import Lycan
from game.roles.superwolf import Superwolf
from game.roles.fox import Fox

def get_role_type(name):
    for role in (Villager, Werewolf, Seer, Guard, Lycan, Superwolf, Fox):
        if role.__name__ == name:
            return role
