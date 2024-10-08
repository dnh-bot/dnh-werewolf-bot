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
from game.roles.pathologist import Pathologist
from game.roles.apprenticeseer import ApprenticeSeer
from game.roles.diseased import Diseased
from game.roles.rat import Rat
from game.roles.cursed import Cursed
from game.roles.harlot import Harlot
import utils


role_info = utils.common.read_json_file("json/role_info.json")


def get_all_roles():
    return Villager, Werewolf, Seer, Guard, Lycan, Superwolf, Betrayer, Fox, Witch, Zombie, Cupid, Chief, Hunter,\
        Tanner, Pathologist, Diseased, Rat, ApprenticeSeer, Cursed, Harlot


def get_party_roles_list():
    party_roles_list = [[], [], []]
    for a_role in get_all_roles():
        _name = a_role.__name__
        field_name = f"name_{TEXT_LANGUAGE}"
        title = _name if field_name not in role_info[_name] else f"{_name} ({role_info[_name][field_name]})"
        party_roles_list[role_info[_name]["party"] - 1].append(title)

    return party_roles_list


def get_role_type(name):
    for role in get_all_roles():
        if role.__name__ == name:
            return role
    print("Unknown state get_role_type")
    return None


def get_role_data_by_name(name):
    name_lower = name.lower()
    for _name, _data in role_info.items():
        if _name.lower() == name_lower:
            field_name = f"name_{TEXT_LANGUAGE}"
            return {
                "title": _name if field_name not in _data else f"{_name} ({_data[field_name]})",
                "party": _data["party"],
                "description": _data["description"][TEXT_LANGUAGE],
                "nighttime_commands": _data["nighttime_commands"]
            }

    return None


def get_role_title(name):
    role_data = get_role_data_by_name(name)
    if role_data is not None:
        return role_data["title"]

    return None


def get_role_description(name):
    role_data = get_role_data_by_name(name)
    if role_data is not None:
        return role_data["description"]

    return None


def get_role_nighttime_commands(name):
    role_data = get_role_data_by_name(name)
    if role_data is not None:
        return role_data["nighttime_commands"]

    return []
