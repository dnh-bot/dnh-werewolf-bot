import time
import asyncio

import interface
from game import *

def assert_players(game, alive_list):
    p = [player.player_id for player in game.players.values() if player.is_alive()]
    print("++++++++++++++++++++", p, alive_list)
    return set(p) == set(alive_list)

async def test_case_simulated_players(game):
        print("====== Begin test case =====")
        DELAY_TIME = 3
        await game.add_player(1, "W")
        await game.add_player(2, "S")
        await game.add_player(3, "V1")
        await game.add_player(4, "V2")
        players = {
            1: roles.Werewolf(game.interface, 1, "W"),
            2: roles.Seer(game.interface,     2, "S"),
            3: roles.Villager(game.interface, 3, "V1"),
            4: roles.Villager(game.interface, 4, "V2"),
        }
        game.set_timer_phase([1,1,1])

        await game.start(players)
        assert assert_players(game, [1,2,3,4])
        
        print(await game.do_player_action("vote", 1, 2))
        print(await game.do_player_action("vote", 3, 2))
        print(await game.do_player_action("vote", 4, 1))

        # await game.next_phase_cmd()  # go NIGHT
        # await game.run_game_loop()
        print("-=0-0------------------")
        time.sleep(DELAY_TIME)
        await game.next_phase_cmd()  # go NIGHT
        # time.sleep(DELAY_TIME)
        assert assert_players(game, [1,2])
        # print(game.display_alive_player())
        
        print(await game.do_player_action("kill", 1, 3))

        # await game.next_phase()  # go DAY
        # time.sleep(DELAY_TIME)

        # await game.next_phase()
        # time.sleep(DELAY_TIME)
        await game.stop()
        # time.sleep(DELAY_TIME)
        print("====== End test case =====")

async def vote(game, author_id, target_id):
    author = game.players.get(author_id)
    target = game.players.get(target_id)
    return await game.vote(author, target)

async def test_game():
    game = Game(None, interface.ConsoleInterface(None))
    await test_case_simulated_players(game)

async def main():
    task = asyncio.create_task(test_game())
    done, pending = await asyncio.wait({task})

    if task in done:
        print("DONE")

if __name__ == '__main__':
    # asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(loop))
    # loop.close()
    # task_game_loop = asyncio.create_task(test_game(), name="test_task")
    asyncio.run(test_game())
    # loop = asyncio.get_event_loop()
    # future = asyncio.run_coroutine_threadsafe(test_game(), loop)
    # result = future.result()
    print("END=======")
