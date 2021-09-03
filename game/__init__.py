# Use OOP or FP here

import datetime
import random
import time
from enum import Enum
import asyncio

import config
from game import roles

class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2


game_state = {
    'start_time': None,
    'current_phase': None,  # GamePhase's property [Day, Night]
    'players': []
}

def run(f, *a, **kw):
    if asyncio.iscoroutinefunction(f):
        loop = asyncio.get_event_loop()
        r = loop.run_until_complete(f(*a, **kw))
        loop.close()
        return r
    else:
        return f(*a, **kw)

class Game:
    def __init__(self, guild, interface):
        self.guild = guild
        self.interface = interface
        self.channels = [
                config.LOBBY_CHANNEL,
                config.GAMEPLAY_CHANNEL,
                config.WEREWOLF_CHANNEL,
                # Personal channel will goes into role class
        ] # List of channels in game
        self.reset_game_state()
        self.next_flag = asyncio.Event()



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
        doctor=1
        r.update((id_, roles.Werewolf(id_)) for id_ in ids[:werewolf])
        r.update((id_, roles.Seer(id_)) for id_ in ids[werewolf:werewolf+seer])
        r.update((id_, roles.Doctor(id_)) for id_ in ids[werewolf+seer: werewolf+seer+doctor])
        r.update((id_, roles.Villager(id_)) for id_ in ids[werewolf+seer+doctor:])
        print("Player list:", r)
        return r


    def start(self):
        if not self.is_stopped:
            self.interface.send_text_to_channel("======= Game started =======", config.GAMEPLAY_CHANNEL)
            self.players = self.generate_roles(self.player_id)

            self.interface.create_channel(config.LOBBY_CHANNEL)
            self.interface.create_channel(config.GAMEPLAY_CHANNEL)
            self.interface.create_channel(config.WEREWOLF_CHANNEL)

            self.start_time = datetime.datetime.now()

            self.game_phase = GamePhase.DAY

            # FIXME: Error unable to run
            run(self.start_game_loop)
            print("End start")




    def stop(self):
        print("======= Game stopped =======")
        self.is_stopped = True
        self.reset_game_state()

    def add_player(self, id_):
        print("Player", id_, "joined")
        self.player_id.append(id_)

    def remove_player(self, id_):
        print("Player", id_, "left")
        self.player_id.remove(id_)

    def get_alive_players(self):
        return [
            player
            for _id, player in self.players.items()
            if player.status.is_alive()
        ]

    def start_game_loop(self):
        print("Started game loop")
        while not self.is_stopped:
            print("Phase:", self.game_phase)
            if self.end_game():
                break
            if self.game_phase == GamePhase.DAY:
                self.do_daytime_phase()
            elif self.game_phase == GamePhase.NIGHT:
                    self.do_daytime_phase()

            for _,role in self.players.items():
                role.on_phase(self.game_phase)

            # Wait for `!next` from Admin
            # or Next phase control from bot
            # self.event.wait()
            # self.next_flag.wait()
            # self.next_flag.clear()
            time.sleep(5)
        print("End start loop")
        # await asyncio.sleep(0)



    def reset_game_state(self):
        # TODO: wrap these variables into a struct
        self.is_stopped = False
        self.start_time = None
        self.players = {}  # id: Player
        self.player_id = []
        self.game_phase = GamePhase.NEW_GAME
        self.killed_last_night = [] # List of player id who was killed last night


    def end_game(self):
        # if end_game_condition_match:
        if False: #FIXME: Check end game condition @Sher
            self.interface.send_text_to_channel("Game end!", config.GAMEPLAY_CHANNEL)
            # if any(werewolf.is_alive() for werewolf in self.players if  isinstance(role, roles.Werewolf)):
            #     self.interface.send_text_to_channel("Werewolf is winner", config.GAMEPLAY_CHANNEL)
            # else:
            #     self.interface.send_text_to_channel("Village is winner", config.GAMEPLAY_CHANNEL)
            reset_game_state()

    def do_nighttime_phase(self):
        self.interface.send_text_to_channel("It's night time, everybody goes to sleep", config.GAMEPLAY_CHANNEL)
        # no need to mute, it's done in role.on_phase
        self.interface.send_text_to_channel("Who would you like to kill tonight?", config.WEREWOLF_CHANNEL)
        #TODO
        self.interface.send_text_to_channel("List of alive player to poll", config.WEREWOLF_CHANNEL)



    def do_daytime_phase(self):
        killed = len(self.killed_last_night)
        self.interface.send_text_to_channel("It's daytime, let's discuss to find the werewolf", config.GAMEPLAY_CHANNEL)
        if killed:
            self.interface.send_text_to_channel("Last night, {} people were killed".format(killed), config.GAMEPLAY_CHANNEL)

        # vote will be pm in role.on_phase

    def next_phase(self):
        print("Next phase")
        assert self.game_phase != GamePhase.NEW
        if self.game_phase == GamePhase.DAY:
            self.game_phase = GamePhase.NIGHT
        elif self.game_phase == GamePhase.NIGHT:
            self.game_phase = GamePhase.DAY
        else:
            print("Incorrect game flow")
        loop.call_soon_threadsafe(self.next_flag.set)



    def test_game(self):
        print("====== Begin test game =====")
        self.add_player(1)
        self.add_player(2)
        self.add_player(3)
        self.add_player(4)
        self.start()
        time.sleep(5)
        self.next_phase()
        time.sleep(5)
        self.next_phase()
        time.sleep(5)
        self.next_phase()
        self.stop()
        print("====== End test game =====")

class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list[guild_id]

class ConsoleInterface:
    def create_channel(self, channel_name):
        print("Created channel #"+channel_name)
    
    def send_text_to_channel(self, text, channel_name):
        print("In #"+channel_name+": "+text)

if __name__ == '__main__':
    game = Game()
