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
        DELAY_TIME = 0.1
        game.timer_enable = False  # MUST have

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


        await game.start(players)
        await asyncio.sleep(DELAY_TIME)
        assert assert_players(game, [1,2,3,4])

        print(await game.do_player_action("vote", 1, 2))
        print(await game.do_player_action("vote", 3, 2))
        print(await game.do_player_action("vote", 4, 1))
        await asyncio.sleep(DELAY_TIME)

        await game.next_phase()  # go NIGHT
        await asyncio.sleep(DELAY_TIME)
        assert assert_players(game, [1,3,4])

        print(await game.do_player_action("kill", 1, 3))
        await asyncio.sleep(DELAY_TIME)

        await game.next_phase()  # go DAY
        await asyncio.sleep(DELAY_TIME)
        assert assert_players(game, [1,4])

        await game.next_phase()
        await asyncio.sleep(DELAY_TIME)
        assert game.is_end_game()

        await game.stop()
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
    asyncio.run(test_game())
    print("END=======")
