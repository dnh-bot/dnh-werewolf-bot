
import utils
import generate_roles
role_config = utils.common.read_json_file("json/role_config.json")
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

def dict_to_list(cfg, number=0):
            yield from (name for name in cfg for _ in range(cfg[name]))
            yield from ('Werewolf' if i % 4 == 0 else 'Villager' for i in range(number - sum(cfg.values())))


# print(role_config)
for roles in role_config:
    print("="*20)
    print(roles)
    # role_list = list([k]v for k,v in roles)
    role_list = list(dict_to_list(roles))
    print(role_list)
    score = generate_roles.get_score(role_dict, role_list)
    print(score)
