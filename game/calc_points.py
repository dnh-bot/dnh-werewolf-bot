import utils
from game import generate_roles

role_config = utils.common.read_json_file("../json/role_config.json")


def dict_to_list(cfg, number=0):
    yield from (name for name in cfg for _ in range(cfg[name]))
    yield from ('Werewolf' if i % 4 == 0 else 'Villager' for i in range(number - sum(cfg.values())))


# print(role_config)
for roles in role_config:
    print("=" * 20)
    print(roles)
    # role_list = list([k]v for k,v in roles)
    role_list = list(dict_to_list(roles))
    print(role_list)
    score = generate_roles.get_score(role_list)
    print(score)
