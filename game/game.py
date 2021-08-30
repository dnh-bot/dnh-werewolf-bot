'''Use OOP or FP here'''

import datetime

player_id = []
game_state = {
    'start_time': None,
    'current_phase': None, # Day, Night, Roles
    'players': []
}


def add_player(id):
    player_id.append(id)

def remove_player(id):
    player_id.remove(id)

def start():
    for id in player_id:
        game_state['players'].append(roles.random(id))
    
    sort_roles(game_state['players'])

    game_state['start_time'] = datetime.now()
    start_game_loop()


def stop():
    stopped = True
    reset(game_state)


def start_game_loop():
    pass


async def game_loop():
    while not stopped:
        for phase in ('day', 'night', 'role'):
            for role in game_state['players']:
                role.on_phase(phase)
            if phase == 'night':
                poll_id = client.show_poll(game.werewolf_channel, game.get_alive_players())
                result = await client.get_poll_result(poll_id)
                game['players'].get(result.player).status = 'killed'

        if end_game(game_state):
            break




