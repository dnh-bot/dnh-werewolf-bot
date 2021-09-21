import time
import asyncio

import interface
from game import *

def assert_players(game, alive_list):
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    print("++++++++++++++++++++", p, alive_list)
    return set(p) == set(alive_list)


async def vote(game, author_id, target_id):
    author = game.players.get(author_id)
    target = game.players.get(target_id)
    return await game.vote(author, target)


async def test_case(game, case_id):
    test_case_data = None
    with open(f"testcases/case{case_id}.json", "r") as fi:
        test_case_data = json.load(fi)

    assert test_case_data is not None

    print("====== Begin test case =====")
    DELAY_TIME = 0.1
    game.timer_enable = False  # MUST have

    player_name_list = sorted(test_case_data["player_list"])  # NOTE: player_list must be a list to prevent out of order
    for player_id, (player_name, player_role) in enumerate(player_name_list, 1):
        print(player_id, player_name, player_role)
        await game.add_player(player_id, player_name)

    # FIXME
    players = {
        player_id: roles.get_role_type(player_role)(game.interface, player_id, player_name)
        for player_id, (player_name, player_role) in enumerate(player_name_list, 1)
    }
    await game.start(players)

    timeline_action_list = test_case_data["timeline"]
    for timeline_idx, action_data in enumerate(timeline_action_list):
        await asyncio.sleep(DELAY_TIME)

        assert assert_players(game, list(map(int, action_data["alive"])))
        for action_str in action_data["action"]:
            author_id, command, target_id = action_str.split()
            print(await game.do_player_action(command, int(author_id), int(target_id)))

        await game.next_phase()

    await asyncio.sleep(DELAY_TIME)
    assert game.is_end_game()

    await game.stop()
    print("====== End test case =====")


async def test_game():
    game = Game(None, interface.ConsoleInterface(None))
    await test_case(game, 1)


async def main():
    task = asyncio.create_task(test_game())
    done, pending = await asyncio.wait({task})

    if task in done:
        print("DONE")


if __name__ == '__main__':
    asyncio.run(test_game())
    print("END=======")
