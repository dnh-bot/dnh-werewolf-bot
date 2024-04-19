import statistics

import utils
from game import generate_roles

def calc_roles():
    role_config = utils.common.read_json_file("json/role_config.json")

    # print(role_config)
    for roles in role_config:
        print("=" * 20)
        print(roles)
        # role_list = list([k]v for k,v in roles)
        role_list = list(utils.common.dict_to_list(roles))
        print(role_list)
        score = generate_roles.get_score(role_list)
        print(score)


def evaluate_system():
    scores = []
    for i in range(1,1000):
        for players in range(4,20):
            role_config = generate_roles.generate_roles_new_strategy([0]*players)
            # if i == 1:
            #     print(role_config)
            score = generate_roles.get_score(role_config)
            scores.append(score)
    # Caculate standard deviation of scores:
    print("Mean score: ", sum(scores)/len(scores))
    print("Max score: ", max(scores))
    print("Min score: ", min(scores))
    print("Standard deviation: ", statistics.stdev(scores))


if __name__ == '__main__':
    calc_roles()
    evaluate_system()
