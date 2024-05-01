import random
from collections import Counter

import utils


generator_info = utils.common.read_json_file("json/role_generator_info.json")
role_dict = generator_info['role_score']
delta = generator_info['delta']


def get_score(generated_roles):
    return sum(role_dict[r] for r in generated_roles)

def add_additional_roles(role_list, num_of_players):
    ignored_roles = ["Werewolf", "Seer", "Guard", "Villager", "Lycan"]
    # From lowest to highest score roles
    fixed_additional_roles = sorted([role for role, score in role_dict.items() if role not in ignored_roles], key=lambda x: role_dict[x])
    additional_roles = [role for role in fixed_additional_roles if role not in role_list[:num_of_players]]
    lycan_amount = role_list.count("Lycan")

    # Replace boring Villager/Lycan
    for role in additional_roles:
        for i in range(num_of_players):
            if (role_list[i] == "Villager") or (role_list[i] == "Lycan" and lycan_amount > 2): # 2 Lycans are enough fun
                role_list[i] = role
                break

    return role_list

def generate_roles_new_strategy(ids):
    num_of_players = len(ids)

    fixed_roles = ["Werewolf", "Seer", "Guard", "Villager"]
    if num_of_players == 4:
        return dict(Counter(fixed_roles))

    role_list = list(r for r in role_dict if r not in fixed_roles)

    num_of_players = num_of_players - len(fixed_roles)

    while len(role_list) < num_of_players * 2:
        role_list += ["Werewolf", "Lycan"] + ["Villager"] * 2

    random.shuffle(role_list)

    scores = abs(get_score(fixed_roles + role_list[:num_of_players]))

    while scores > delta:
        random.shuffle(role_list)
        scores = get_score(fixed_roles + role_list[:num_of_players])

    if num_of_players >= 3:
        # Handle boring & useless Villagers :D
        role_list = add_additional_roles(role_list, num_of_players)

    total_players = len(ids)
    total_wolves = role_list[:num_of_players].count("Werewolf") + role_list[:num_of_players].count("Superwolf") + 1

    # Limit werewolves
    while (total_wolves > 4) or (total_players <= 9 and total_wolves > 2) or (total_players <= 7 and total_wolves >= 2):
        if "Werewolf" in role_list[:num_of_players]:
            role_list.remove("Werewolf")
        total_wolves -= 1

    return dict(Counter(fixed_roles + role_list[:num_of_players]))
