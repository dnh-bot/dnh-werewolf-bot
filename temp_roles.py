import random
from collections import Counter

def get_score(role_dict, generated_roles):
    return sum(role_dict[r] for r in generated_roles)

def check_ratio_roles(roles):
    wolf_party = ['Werewolf', 'Superwolf', 'Betrayer']
    third_party = ['Tanner', 'Cupid', 'Fox']
    count_wolf, count_third_part = 0, 0
    for role in roles:
        if role in wolf_party:
            count_wolf += roles[role]
        elif role in third_party:
            count_third_part += roles[role]
    return count_wolf, count_third_part

def generate_roles_new_strategy(ids):
    num_of_players = len(ids)
    meta_data = {'Nums players': num_of_players}
    fixed_roles = ['Werewolf', 'Seer', 'Guard', 'Villager']
    if num_of_players == 4:
        return dict(Counter(fixed_roles))
    role_dict = {
    "Seer": 4,
    "Witch": 5,
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
    "Werewolf": -5,
    "Superwolf": -6
  }
    delta = 2
    role_list = list(r for r in role_dict if r not in fixed_roles)

    num_of_players = num_of_players - len(fixed_roles)

    while len(role_list) < num_of_players:
        role_list += ['Werewolf', 'Lycan', 'Villager'] * 2

    random.shuffle(role_list)
    print("ROLE LIST", role_list)
    random.shuffle(role_list)

    scores = abs(get_score(role_dict, fixed_roles + role_list[:num_of_players]) - 2)

    while scores > delta:
        random.shuffle(role_list)
        scores = abs(get_score(role_dict, fixed_roles + role_list[:num_of_players]) - 2)
    meta_data['Scores'] = scores
    roles = dict(Counter(fixed_roles + role_list[:num_of_players]))
    count_wolf, count_third_part = check_ratio_roles(roles)
    meta_data['Number of wolves'] = count_wolf
    meta_data['Number of third party'] = count_third_part
    return {**meta_data, **roles}

res = []
for i in range(5, 30):
    for j in range(10):
        ids = [0] * i
        temp = generate_roles_new_strategy(ids)
        print(temp)
        res.append(temp)
