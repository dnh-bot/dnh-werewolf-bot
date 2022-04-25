import time
import asyncio
import os

import interface
from game import *

def assert_time_print(filepath, game, playersname):
    print("\n\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(f"Failed at test case {filepath}\n")
    print(f"Test assert Error at {'#day' if {game.game_phase} else '#night'}{game.day}")
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    print(f"Current alive player: {list(map(lambda x: playersname[x], p))}")
    print(f"Winner: {game.get_winner()}")
    print("\n\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")


def check_alive_players(game, alive_list, playersname):
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    # print("++++++++++++++++++++\nids: ", p, alive_list)
    print(f"\nAlive user list:\n game:     {list(map(lambda x: playersname[x], p))}\n expected: { list(map(lambda x: playersname[x], alive_list))}")
    return set(p) == set(alive_list)


def check_game_end(game, win):
    if not win:  # If test case does not define "win", then it must end.
        return game.get_winner() is not None
    else:
        return game.get_winner() == win


def assign_roles(interface, ids, names_dict, game_role):
    return {id_: roles.get_role_type(role_name)(interface, id_, names_dict[id_]) for id_, role_name in zip(ids, game_role)}


async def test_case(game, filepath):
    test_case_data = None
    with open(filepath, "r") as fi:
        test_case_data = json.load(fi)

    try:
        assert test_case_data is not None

        print(f"\n\n\n====== Begin test case at {filepath} =====")
        print(f"Test case: {test_case_data['name']}")
        DELAY_TIME = 0.03  # MUST greater than 0
        game.timer_enable = False  # MUST have

        player_name_dict = test_case_data["player_list"]  # username: Role
        playersname = {}  # id: username
        game_role = []  # ["Werewolf", "Seer","Villager","Villager",]
        for player_id, player_name in enumerate(player_name_dict, 1):
            playersname[player_id] = player_name  # Offset by 1 to prevent player id = 0
            game_role.append(player_name_dict[player_name])

        # Revert name -> ID map for reference
        id_map = {v: k for k, v in playersname.items()}  # username: id

        players = assign_roles(game.interface, list(playersname.keys()), playersname, game_role)
        await game.start(players)

        timeline_action_list = test_case_data["timeline"]
        for timeline_idx, action_data in enumerate(timeline_action_list):
            await asyncio.sleep(DELAY_TIME)

            assert check_alive_players(game, list(map(lambda x: id_map[x], action_data["alive"])), playersname)
            for action_str in action_data["action"]:
                author_name, command = action_str.split()[:2]
                target_name = action_str.split()[2:]
                print(await game.do_player_action(command, id_map[author_name], *[id_map[i] for i in target_name]))
            await asyncio.sleep(DELAY_TIME)
            await game.next_phase()

        await asyncio.sleep(DELAY_TIME)
        assert check_game_end(game, test_case_data.get("win"))

        await asyncio.sleep(DELAY_TIME)
        await game.stop()
        print("====== End test case =====")
    except AssertionError as e:
        assert_time_print(filepath, game, playersname)
        raise
    except Exception as e:
        print(e)
        raise


async def test_game():
    game = Game(None, interface.ConsoleInterface(None))

    # Run single test
    
    await test_case(game, "./testcases/case-zombie-simple.json")

    # Run all tests
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


if __name__ == "__main__":
    asyncio.run(test_game())
    print("END=======")
