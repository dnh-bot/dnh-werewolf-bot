import random
from collections import Counter

def get_score(role_dict, generated_roles):
    return sum(role_dict[r] for r in generated_roles)

def generate_roles_new_strategy(ids):
    num_of_players = len(ids)

    fixed_roles = ['Werewolf', 'Seer', 'Guard', 'Villager']
    if num_of_players == 4:
        return dict(Counter(fixed_roles))
    role_dict = {
        "Seer": 7,
        "Witch": 6,
        "Guard": 3,
        "Hunter": 3,
        "Zombie": 3,
        "Chief": 2,
        "Villager": 1,
        "Tanner": 1,
        "Lycan": -1,
        "Fox": -1,
        "Betrayer": -2,
        "Cupid": -3,
        "Werewolf": -6,
        "Superwolf": -7,
    }
    delta = 5
    role_list = list(r for r in role_dict if r not in fixed_roles)

    num_of_players = num_of_players - len(fixed_roles)

    while len(role_list) < num_of_players*2:
        role_list += ['Werewolf', 'Lycan'] + ['Villager']*2

    random.shuffle(role_list)

    scores = get_score(role_dict, fixed_roles + role_list[:num_of_players])

    while scores < delta or scores > 7 :
        scores = get_score(role_dict, fixed_roles + role_list[:num_of_players])
        random.shuffle(role_list)
    return dict(Counter(fixed_roles + role_list[:num_of_players]))
