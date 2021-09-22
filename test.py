import time
import asyncio
import os

import interface
from game import *

def assert_players(game, alive_list, playersname):
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    # print("++++++++++++++++++++\nids: ", p, alive_list)
    print("users: ", list(map(lambda x: playersname[x], p)), list(map(lambda x: playersname[x], alive_list)))
    return set(p) == set(alive_list)


def assign_roles(interface, ids, names_dict, game_role):
    return {id_: roles.get_role_type(role_name)(interface, id_, names_dict[id_]) for id_,role_name in zip(ids, game_role)}


async def test_case(game, filepath):
    test_case_data = None
    with open(filepath, "r") as fi:
        test_case_data = json.load(fi)

    assert test_case_data is not None

    print(f"\n\n\n====== Begin test case at {filepath} =====")
    print(f"Test case: {test_case_data['name']}")
    DELAY_TIME = 0.1
    game.timer_enable = False  # MUST have

    player_name_dict = test_case_data["player_list"]  # username: Role
    playersname = {}  # id: username
    game_role = []  # ["Werewolf", "Seer","Villager","Villager",]
    for player_id, player_name in enumerate(player_name_dict):
        playersname[player_id] = player_name
        game_role.append(player_name_dict[player_name])

    # Revert name -> ID map for reference
    id_map = {v: k for k, v in playersname.items()}  # username: id

    players = assign_roles(game.interface, list(playersname.keys()), playersname, game_role)
    await game.start(players)

    timeline_action_list = test_case_data["timeline"]
    for timeline_idx, action_data in enumerate(timeline_action_list):
        await asyncio.sleep(DELAY_TIME)

        assert assert_players(game, list(map(lambda x: id_map[x], action_data["alive"])), playersname)
        for action_str in action_data["action"]:
            author_name, command, target_name = action_str.split()
            print(await game.do_player_action(command, id_map[author_name], id_map[target_name]))
        await asyncio.sleep(DELAY_TIME)
        await game.next_phase()

    await asyncio.sleep(DELAY_TIME)
    assert game.is_end_game()

    await game.stop()
    print("====== End test case =====")


async def test_game():
    game = Game(None, interface.ConsoleInterface(None))
    directory = "testcases"
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            path = os.path.join(directory, filename)
            await test_case(game, path)
        else:
            continue


async def main():
    task = asyncio.create_task(test_game())
    done, pending = await asyncio.wait({task})

    if task in done:
        print("DONE")


if __name__ == '__main__':
    asyncio.run(test_game())
    print("END=======")
