import random
from collections import Counter

import utils


generator_info = utils.common.read_json_file("json/role_generator_info.json")
role_dict = generator_info['role_score']
delta = generator_info['delta']


def get_score(generated_roles):
    return sum(role_dict[r] for r in generated_roles)


def generate_roles_new_strategy(ids):
    num_of_players = len(ids)

    fixed_roles = ['Werewolf', 'Seer', 'Guard', 'Villager']
    if num_of_players == 4:
        return dict(Counter(fixed_roles))

    role_list = list(r for r in role_dict if r not in fixed_roles)

    num_of_players = num_of_players - len(fixed_roles)

    while len(role_list) < num_of_players * 2:
        role_list += ['Werewolf', 'Lycan'] + ['Villager'] * 2

    random.shuffle(role_list)

    scores = abs(get_score(fixed_roles + role_list[:num_of_players]))

    while scores < delta or scores > 7:
        random.shuffle(role_list)
        scores = get_score(fixed_roles + role_list[:num_of_players])
    return dict(Counter(fixed_roles + role_list[:num_of_players]))
