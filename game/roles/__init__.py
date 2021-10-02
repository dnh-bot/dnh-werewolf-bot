import json

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
from game.roles.cupid import Cupid

ROLE_INFO_FILE = "json/role_info.json"


def read_role_info_json():
    try:
        with open(ROLE_INFO_FILE, "r", encoding="utf8") as f:
            print(f"successfully loaded {ROLE_INFO_FILE}")
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


role_info = read_role_info_json()


def get_all_roles():
    return (Villager, Werewolf, Seer, Guard, Lycan, Betrayer, Superwolf, Fox, Witch, Cupid)


def get_role_type(name):
    for role in get_all_roles():
        if role.__name__ == name:
            return role


def get_role_name_in_language(name, language):
    name = name.capitalize()
    field_name = f"name_{language}"
    if name in role_info and field_name in role_info[name]:
        return role_info[name][field_name]


def get_role_description(name):
    name = name.capitalize()
    if name in role_info:
        return role_info[name]["description"][TEXT_LANGUAGE]

    return None


def get_role_nighttime_command(name):
    name = name.capitalize()
    if name in role_info:
        return role_info[name]["nighttime_command"]

    return ""
