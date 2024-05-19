import asyncio
import os

import interface
from game import *


def assert_time_print(filepath, game, playersname):
    print("\n\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(f"Failed at test case {filepath}\n")
    print(f"Test assert Error at {'#day' if game.game_phase==const.GamePhase.DAY else '#night'}{game.day}")
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    print(f"Current alive player: {list(map(lambda x: playersname[x], p))}")
    print(f"Winner: {game.get_winner()}")
    print("\n\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")


def check_alive_players(game, alive_list, playersname):
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    # print("++++++++++++++++++++\nids: ", p, alive_list)
    print(
        f"\nAlive user list:\n game:     {list(map(lambda x: playersname[x], p))}\n expected: { list(map(lambda x: playersname[x], alive_list))}")
    return set(p) == set(alive_list)


def check_game_end(game, win):
    if not win:  # If test case does not define "win", then it must end.
        return game.get_winner() is not None

    return game.get_winner() == win


def assign_roles(game_interface, ids, names_dict, game_role):
    return {id_: roles.get_role_type(role_name)(game_interface, id_, names_dict[id_]) for id_, role_name in zip(ids, game_role)}


async def test_case(game, filepath):
    test_case_data = None
    with open(filepath, "r", encoding="utf8") as fi:
        test_case_data = json.load(fi)

    try:
        assert test_case_data is not None
        print("\n\n\n" + "$" * 150)
        print(f"====== Begin test case at {filepath} =====")
        print(f"Test case: {test_case_data['name']}")
        delay_time = float(os.getenv("TEST_THREAD_DELAY_TIME"))
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
            await asyncio.sleep(delay_time)

            assert check_alive_players(game, list(map(lambda x: id_map[x], action_data["alive"])), playersname)
            for action_str in action_data["action"]:
                expected_result = None
                if action_str.find("=") != -1:
                    action_str, expected_result = action_str.split(" = ")

                author_name, command = action_str.split()[:2]
                target_name = action_str.split()[2:]
                text = await game.do_player_action(command, id_map[author_name], *[id_map[i] for i in target_name])
                print(text)

                if command == "seer":
                    # test example:
                    # "s1 seer v1 = false"
                    # "s1 seer w1 = true"
                    target_seen_as_werewolf = game.players[id_map[target_name[0]]].seer_seen_as_werewolf()
                    assert expected_result.capitalize() == str(target_seen_as_werewolf)

            await asyncio.sleep(delay_time)
            await game.next_phase()

        await asyncio.sleep(delay_time)

        assert check_game_end(game, test_case_data.get("win"))
        if test_case_data.get("win") != "None":
            await game.task_game_loop
        else:
            await asyncio.sleep(delay_time)
        await game.stop()
        print("====== End test case =====")
    except AssertionError:
        assert_time_print(filepath, game, playersname)
        raise
    except Exception as e:
        print(e)
        raise


async def test_game():
    game = Game(None, interface.ConsoleInterface(None))

    # Run single test
    # await test_case(game, "testcases/case-hunter-couple-die-together-by-kill.json")
    # await test_case(game, "testcases/case-hunter-couple-die-together-by-vote.json")
    # await test_case(game, "testcases/case-hunter-hunt-fox.json")
    # await test_case(game, "testcases/case-hunter-hunt-wolf.json")
    # await test_case(game, "testcases/case-hunter-simple.json")
    # await test_case(game, "testcases/case-hunter-hunt-night1.json")
    # await test_case(game, "testcases/case-hunter-hunted-one-in-couple.json")

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
    done, _ = await asyncio.wait({task})

    if task in done:
        print("DONE")


if __name__ == "__main__":
    asyncio.run(test_game())
    print("\n\nFINISH ALL TEST CASES SUCCESSFULLY")
