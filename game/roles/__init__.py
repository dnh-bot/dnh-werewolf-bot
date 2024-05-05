from config import TEXT_LANGUAGE
from game.roles.villager import Villager
from game.roles.werewolf import Werewolf
from game.roles.guard import Guard
from game.roles.seer import Seer
from game.roles.lycan import Lycan
from game.roles.betrayer import Betrayer
from game.roles.superwolf import Superwolf
from game.roles.fox import Fox
from game.roles.witch import Witch
from game.roles.zombie import Zombie
from game.roles.cupid import Cupid
from game.roles.chief import Chief
from game.roles.hunter import Hunter
from game.roles.tanner import Tanner
from game.roles.rat import Rat
import utils


role_info = utils.common.read_json_file("json/role_info.json")


def get_all_roles():
    return Villager, Werewolf, Seer, Guard, Lycan, Betrayer, Superwolf, Fox, Witch, Zombie, Cupid, Chief, Hunter, Tanner, Rat


def get_role_type(name):
    for role in get_all_roles():
        if role.__name__ == name:
            return role
    print("Unknown state get_role_type")
    return None


def get_role_title(name):
    name = name.capitalize()
    if name in role_info:
        field_name = f"name_{TEXT_LANGUAGE}"
        if field_name in role_info[name]:
            return f"{name} ({role_info[name][field_name]})"
        return name
    print("Unknown state get_role_title")
    return None


def get_role_description(name):
    name = name.capitalize()
    if name in role_info:
        return role_info[name]["description"][TEXT_LANGUAGE]

    return None


def get_role_nighttime_commands(name):
    name = name.capitalize()
    if name in role_info:
        return role_info[name]["nighttime_commands"]

    return []
