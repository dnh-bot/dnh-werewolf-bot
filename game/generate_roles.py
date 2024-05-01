import random
from collections import Counter

import utils


generator_info = utils.common.read_json_file("json/role_generator_info.json")
role_dict = generator_info['role_score']
delta = generator_info['delta']


def get_score(generated_roles):
    return sum(role_dict[r] for r in generated_roles)


def add_additional_roles(role_list, remaining_roles):
    ignored_roles = ["Werewolf", "Seer", "Guard", "Villager", "Lycan"]
    # From lowest to highest score roles
    fixed_additional_roles = sorted([role for role in role_dict.keys() if role not in ignored_roles], key=lambda x: role_dict[x])
    additional_roles = [role for role in fixed_additional_roles if role not in role_list[:remaining_roles]]
    lycan_amount = role_list.count("Lycan")

    # Replace boring Villager/Lycan
    for role in additional_roles:
        for i in range(remaining_roles):
            if (role_list[i] == "Villager") or (role_list[i] == "Lycan" and lycan_amount > 2):  # 2 Lycans are enough fun
                role_list[i] = role
                break

    return role_list


def balance_werewolves(total_players, role_list, remaining_roles):
    total_wolves = sum(r in ("Werewolf", "Superwolf") for r in role_list[:remaining_roles]) + 1
    while total_wolves > 4 or \
            (10 <= total_players <= 14 and total_wolves > 3) or \
            (total_players <= 9 and total_wolves > 2) or \
            (total_players <= 6 and total_wolves > 1):
        if "Werewolf" in role_list[:remaining_roles]:
            role_list.remove("Werewolf")
        elif "Superwolf" in role_list[:remaining_roles]:
            role_list.remove("Superwolf")
        total_wolves -= 1

    return role_list


def generate_roles_new_strategy(ids):
    total_players = len(ids)

    fixed_roles = ["Werewolf", "Seer", "Guard", "Villager"]
    if total_players == 4:
        return dict(Counter(fixed_roles))

    role_list = list(r for r in role_dict if r not in fixed_roles)

    remaining_roles = total_players - len(fixed_roles)

    while len(role_list) < remaining_roles * 2:
        role_list += ["Werewolf", "Lycan"] + ["Villager"] * 2

    random.shuffle(role_list)

    scores = abs(get_score(fixed_roles + role_list[:remaining_roles]))

    while scores > delta:
        random.shuffle(role_list)
        scores = get_score(fixed_roles + role_list[:remaining_roles])

    if total_players >= 7:
        # Handle boring & useless Villagers :D
        role_list = add_additional_roles(role_list, remaining_roles)

    # Limit werewolves
    role_list = balance_werewolves(total_players, role_list, remaining_roles)

    return dict(Counter(fixed_roles + role_list[:remaining_roles]))
