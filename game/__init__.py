import datetime
import random
import time
from enum import Enum
import asyncio

import config
from game import roles, text_template


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2


game_state = {
    'start_time': None,
    'current_phase': None,  # GamePhase's property [Day, Night]
    'players': []
}


class Game:
    def __init__(self, guild, interface):
        self.guild = guild
        self.interface = interface
        self.channels = [
            config.LOBBY_CHANNEL,
            config.GAMEPLAY_CHANNEL,
            config.WEREWOLF_CHANNEL,
            # Personal channel will goes into role class
        ]  # List of channels in game
        self.reset_game_state()
        self.next_flag = asyncio.Event()

    def get_guild(self):
        return self.guild

    def is_started(self):
        return (self.game_phase != GamePhase.NEW_GAME)

    def awake(self):
        pass

    # TODO: Sher
    @staticmethod
    def generate_roles(ids):
        ids = ids.copy()
        random.shuffle(ids)
        r = dict()
        l = len(ids)
        werewolf = l//4
        seer = 1
        guard = 1
        r.update((id_, roles.Werewolf(id_)) for id_ in ids[:werewolf])
        r.update((id_, roles.Seer(id_)) for id_ in ids[werewolf:werewolf+seer])
        r.update((id_, roles.Guard(id_)) for id_ in ids[werewolf+seer: werewolf+seer+guard])
        r.update((id_, roles.Villager(id_)) for id_ in ids[werewolf+seer+guard:])
        print("Player list:", r)
        return r

    async def start(self, init_players=None):
        if not self.is_stopped:
            await self.interface.send_text_to_channel(text_template.generate_start_text(), config.GAMEPLAY_CHANNEL)
            if not init_players:
                self.players = self.generate_roles(self.player_id)
            else:
                self.players = init_players

            await self.interface.create_channel(config.LOBBY_CHANNEL)
            await self.interface.create_channel(config.GAMEPLAY_CHANNEL)
            await self.interface.create_channel(config.WEREWOLF_CHANNEL)

            self.start_time = datetime.datetime.now()

            self.game_phase = GamePhase.DAY

            self.task_game_loop = asyncio.create_task(self.start_game_loop())
            print(self.task_game_loop)

    async def stop(self):
        print("======= Game stopped =======")
        self.is_stopped = True
        self.reset_game_state()
        self.task_game_loop.cancel()
        try:
            await self.task_game_loop
        except asyncio.CancelledError:
            print("task_game_loop is cancelled now")

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
            if player.is_alive()
        ]

    def display_alive_player(self):
        return "\n".join((
            "======== Alive players: =======",
            "\n".join(
                map(str,
                [
                    (player.player_id, player.__class__.__name__) 
                    for _id, player in self.players.items()
                    if player.is_alive()
                ]
                )
            ),
            "\n"
        ))


    async def start_game_loop(self):
        text ="Welcome players: "
        for _id, player in self.players.items():
            text += f"<@{_id}>, "
            if isinstance(player, roles.Werewolf):
                print("Wolf: ", player)
                await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL)
                await self.interface.send_text_to_channel(f"Hello werewolf <@{_id}>", config.WEREWOLF_CHANNEL)
        await self.interface.send_text_to_channel(text, config.GAMEPLAY_CHANNEL)
        print("Started game loop")
        while not self.is_stopped:
            print("Phase:", self.game_phase)

            # New phase
            await self.new_phase()

            for _, role in self.players.items():
                role.on_phase(self.game_phase)

            # Wait for `!next` from Admin
            # or Next phase control from bot
            await self.next_flag.wait()
            self.next_flag.clear()

            await self.end_phase()
            # End_phase

            print("End phase")
            if await self.end_game():
                break;
        print("End start loop")

    def reset_game_state(self):
        # TODO: wrap these variables into a struct
        self.is_stopped = False
        self.start_time = None
        self.players = {}  # id: Player
        self.player_id = []
        self.game_phase = GamePhase.NEW_GAME
        self.killed_last_night = [] # List of player id who was killed last night
        self.lynched_last_day = []
        self.day = 0

    async def end_game(self):
        num_werewolf = 0
        num_players = 0
        for _, player in self.players.items():
            if player.is_alive():
                num_players +=1
                # FIXME: better use of type
                if isinstance(player, roles.Werewolf):
                    num_werewolf +=1
        print("DEBUG: ", num_players, num_werewolf)

        if (num_werewolf/num_players >= 0.5) or (num_werewolf == 0):
            if any(werewolf.is_alive() for _,werewolf in self.players.items() if  isinstance(werewolf, roles.Werewolf)):
                await self.interface.send_text_to_channel(text_template.generate_endgame_text("Werewolf"), config.GAMEPLAY_CHANNEL)
            else:
                await self.interface.send_text_to_channel(text_template.generate_endgame_text("Villager"), config.GAMEPLAY_CHANNEL)
            # Print werewolf list:
            werewolf_list = ",".join([str(f"<@{_id}>") for _id, werewolf in self.players.items() if  isinstance(werewolf, roles.Werewolf)])
            await self.interface.send_text_to_channel("Werewolfs: "+werewolf_list, config.GAMEPLAY_CHANNEL)

            self.reset_game_state()
            return True
        else:
            return False


    @staticmethod
    def get_top_voted(list_id):
        from collections import Counter
        top_voted=Counter(list_id).most_common(2)
        if len(top_voted)==1 or (len(top_voted)==2 and top_voted[0][1]>top_voted[1][1]):
            return top_voted[0][0]
        return None # have no vote or equal voted

    async def do_new_daytime_phase(self):
        self.day += 1
        alive_player = ", ".join(
            f"<@{id_}>" for id_ in self.players if self.players[id_].is_alive()
        )
        await self.interface.send_text_to_channel(text_template.generate_day_phase_beginning_text(self.day, alive_player), config.GAMEPLAY_CHANNEL)

    async def do_end_daytime_phase(self):
        lynched = Game.get_top_voted(self.lynched_last_day)
        print("lynced list:",self.lynched_last_day)
        self.lynched_last_day = []
        if lynched:
            self.players[lynched].get_killed()
            await self.interface.send_text_to_channel(text_template.generate_lynch_text(f"<@{lynched}>"), config.GAMEPLAY_CHANNEL)

    async def do_new_nighttime_phase(self):
        await self.interface.send_text_to_channel(text_template.generate_night_phase_beginning_text(), config.GAMEPLAY_CHANNEL)
        # no need to mute, it's done in role.on_phase
        await self.interface.send_text_to_channel(text_template.generate_before_voting_werewolf(), config.WEREWOLF_CHANNEL)
        # TODO
        # await self.interface.send_text_to_channel("List of alive player to poll", config.WEREWOLF_CHANNEL)

    async def do_end_nighttime_phase(self):
        #TODO: logic for other role as guard, hunter...?
        killed = Game.get_top_voted(self.killed_last_night)
        self.killed_last_night = []
        if killed:
            self.players[killed].get_killed()
            await self.interface.send_text_to_channel(text_template.generate_killed_text([f"<@{killed}>"]), config.GAMEPLAY_CHANNEL)

    async def new_phase(self):
        print(self.display_alive_player())
        if self.game_phase == GamePhase.DAY:
            await self.do_new_daytime_phase()
        elif self.game_phase == GamePhase.NIGHT:
            await self.do_new_nighttime_phase()

    async def end_phase(self):
        assert self.game_phase != GamePhase.NEW_GAME
        if self.game_phase == GamePhase.DAY:
            await self.do_end_daytime_phase()
        elif self.game_phase == GamePhase.NIGHT:
            await self.do_end_nighttime_phase()

        if self.game_phase == GamePhase.DAY:
            self.game_phase = GamePhase.NIGHT
        elif self.game_phase == GamePhase.NIGHT:
            self.game_phase = GamePhase.DAY
        else:
            print("Incorrect game flow")

    async def next_phase(self):
        print("Next phase")
        asyncio.get_event_loop().call_soon_threadsafe(self.next_flag.set)

    async def vote(self, author_id, player_id):
        author = self.players[author_id]
        if not author.is_alive():
            return "You must be alive to vote!"

        self.lynched_last_day.append(player_id)
        #TODO: get user name
        return f"{author_id} voted to kill {player_id}"


    async def kill(self, author_id, player_id):
        assert self.players is not None
        print(self.players)
        author = self.players[author_id]
        if not author.is_alive() or not isinstance(author, roles.Werewolf):
            return "You must be an alive werewolf to kill!"
        self.killed_last_night.append(player_id)
        #TODO: get user name
        return f"{author_id} decided to kill {player_id}"


    async def test_game(self):
        print("====== Begin test game =====")
        DELAY_TIME=3
        self.add_player(1)
        self.add_player(2)
        self.add_player(3)
        self.add_player(4)
        players = {
            1:roles.Werewolf(1),
            2:roles.Villager(2),
            3:roles.Villager(3),
            4:roles.Villager(4),
        }
        await self.start(players)
        print(await self.vote(1,2))
        print(await self.vote(3,2))

        await self.next_phase()  # go NIGHT
        await asyncio.sleep(DELAY_TIME)
        print(await self.kill(1,3))

        await self.next_phase()  # go DAY
        await asyncio.sleep(DELAY_TIME)

        await self.next_phase()
        await asyncio.sleep(DELAY_TIME)
        await self.stop()
        print("====== End test game =====")


class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list[guild_id]


if __name__ == '__main__':
    game = Game()
