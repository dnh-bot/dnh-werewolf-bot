# Use OOP or FP here

import datetime
from enum import Enum


class GamePhase(Enum):
    DAY = 1
    NIGHT = 2
    ROLES = 3


game_state = {
    'start_time': None,
    'current_phase': None,  # Day, Night, Roles
    'players': []
}


class Game:
    def __init__(self, guild):
        self.guild = guild
        self.is_stopped = False
        self.start_time = None
        self.players = {}  # id: Player
        self.player_id = []

    def get_guild(self):
        return self.guild

    def awake(self):
        pass

    def start(self):
        for id_ in self.player_id:
            game_state['players'].append(roles.random(id_))

        sort_roles(game_state['players'])

        self.start_time = game_state['start_time'] = datetime.datetime.now()
        self.start_game_loop()

    def stop(self):
        self.is_stopped = True
        self.reset_game_state()

    def add_player(self, id_):
        self.player_id.append(id_)

    def remove_player(self, id_):
        self.player_id.remove(id_)

    def get_alive_players(self):
        return [
            player
            for _id, player in self.players.items()
            if player.status.is_alive()
        ]

    def start_game_loop(self):
        pass

    async def game_loop(self):
        while not self.is_stopped:
            for phase_item in GamePhase:
                phase = phase_item.value

                for role in game_state['players']:
                    role.on_phase(phase)

                if phase == GamePhase.DAY:
                    self.do_daytime_phase()

                if phase == GamePhase.NIGHT:
                    self.do_nighttime_phase()

            if self.end_game():
                break

    def reset_game_state(self):
        pass

    def end_game(self):
        pass

    def do_nighttime_phase(self):
        # werewolves vote 1 person to kill
        # poll_id = client.show_poll(self.werewolf_channel, self.get_alive_players())
        # result = await client.get_poll_result(poll_id)
        # self.players.get(result.player).get_killed()
        pass

    def do_daytime_phase(self):
        # villagers vote 1 person to kill
        # poll_id = client.show_poll(self.gameplay_channel, self.get_alive_players())
        # result = await client.get_poll_result(poll_id)
        # self.players.get(result.player).get_killed()
        pass

class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list[guild_id]

if __name__ == '__main__':
    game = Game()
