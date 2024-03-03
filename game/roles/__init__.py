import re

from config import TEXT_LANGUAGE
from game.roles.character import CharacterStatus
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
import utils


role_info = utils.common.read_json_file("json/role_info.json")


def get_all_roles():
    return (Villager, Werewolf, Seer, Guard, Lycan, Betrayer, Superwolf, Fox, Witch, Zombie, Cupid)


def get_role_type(name):
    for role in get_all_roles():
        if role.__name__ == name:
            return role


def get_role_name_in_language(name, language):
    # TODO: remove this function after complete text_template.json
    return name


def get_role_title(name):
    name = name.capitalize()
    if name in role_info:
        field_name = f"name_{TEXT_LANGUAGE}"
        if field_name in role_info[name]:
            return f"{name} ({role_info[name][field_name]})"

        return name


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


def create_from_str(interface, character_str):
    matcher = re.findall(r"^(\w+)\((\d+),(\d+)(.*)\)$", character_str)
    if not matcher:
        return None

    role_name, player_id, status, kwargs_str = matcher[0]
    role_cls = get_role_type(role_name)
    player_id = int(player_id)
    status = CharacterStatus(int(status))
    if kwargs_str:
        data = re.split(r",(\w+)=", kwargs_str)[1:]
        kwargs = dict(zip(data[0::2], data[1::2]))
    else:
        kwargs = {}

    return role_cls.new(interface, player_id, status, **kwargs)
