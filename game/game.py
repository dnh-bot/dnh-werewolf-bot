# Use OOP or FP here

import datetime
from enum import Enum
import config

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
        self.channels = {
                'lobby': None,
                'gameplay': None,
                'werewolf': None
                # Personal channel will goes into role class
            }

    def get_guild(self):
        return self.guild

    def awake(self):
        pass

    #TODO: Sher
    @staticmethod
    def generate_roles(ids):
        ids = ids.copy()
        random.shuffle(ids)
        r = dict()
        l = len(ids)
        werewolf=l//4
        seer=1
        docter=1
        r.update((id_, roles.Werewolf(id_)) for id_ in ids[:werewolf])
        r.update((id_, roles.Seer(id_)) for id_ in ids[werewolf:werewolf+seer])
        r.update((id_, roles.Docter(id_)) for id_ in ids[werewofl+seer: werewolf+seer+docter])
        r.update((id_, roles.Village(id_)) for id_ in ids[werewolf+seer+docter:])

        return r


    def start(self):
        self.players = self.generate_roles(self.player_id)

        self.channels['lobby'] = commands.create_channel(config.LOBBY_CHANNEL)
        self.channels['gampley'] = commands.create_channel(config.GAMEPLAY_CHANNEL)
        self.channels['werewolf'] = commands.create_channel(config.WEREWOLF_CHANNEL)


        self.start_time = datetime.datetime.now()
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
        while not self.is_stopped:
            for phase_item in GamePhase:
                phase = phase_item.value

                if phase == GamePhase.DAY:
                    self.do_daytime_phase()

                if phase == GamePhase.NIGHT:
                    self.do_nighttime_phase()

                for role in self.players:
                    role.on_phase(phase)

            if self.end_game():
                break

    def reset_game_state(self):
        self.player_id = []
        self.players = {}


    def end_game(self):
        if any(werewolf.is_alive() for werewolf in self.players if  isinstance(role, roles.Werewolf)):
            commands.send_text_to_channel("Werewolf is winner", self.channels['gameplay'])
        else:
            commands.send_text_to_channel("Village is winner", self.channels['gameplay'])
        reset_game_state()

    def do_nighttime_phase(self):
        commands.send_text_to_channel("It's night time, everybody goes to sleep", self.channels["gameplay"])
        # no need to mute, it's done in role.on_phase
        commands.send_text_to_channel("Who would you like to kill tonight?", self.channels['werewolf'])
        #TODO
        commands.send_text_to_channel("List of alive player to poll", self.channels['werewolf'])



    def do_daytime_phase(self):
        killed = len(self.states.killed_last_night)
        commands.send_text_to_channel("It's daytime, let's discuss to find the werewolf", self.channels['gameplay'])
        if killed:
            commands.send_text_to_channel("Last night, {} people were killed".format(killed), self.channels['gameplay'])

        # vote will be pm in role.on_phase

class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list[guild_id]

if __name__ == '__main__':
    game = Game()
