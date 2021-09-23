import config
from game import roles, text_template

import datetime
import random
import time
from enum import Enum
import asyncio
from collections import Counter
from functools import reduce
import json


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2


class Game:
    def __init__(self, guild, interface):
        self.guild = guild  # Should not use. Reserved for future.
        self.interface = interface
        self.channels = [
            config.LOBBY_CHANNEL,
            config.GAMEPLAY_CHANNEL,
            config.WEREWOLF_CHANNEL,
            # Personal channel will goes into role class
        ]  # List of channels in game
        self.next_flag = asyncio.Event()
        self.timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
        self.timer_enable = True

        self.reset_game_state()  # Init other game variables every end game.

    def reset_game_state(self):
        print("reset_game_state")
        self.is_stopped = True
        self.start_time = None
        self.players = {}  # id: Player
        self.playersname = {}  # id: username
        self.game_phase = GamePhase.NEW_GAME
        self.wolf_kill_dict = {}  # dict[wolf] -> player
        self.reborn_set = set()
        self.night_pending_kill_list = []
        self.voter_dict = {}  # Dict of voted players {user1:user2, user3:user4, user2:user1}. All items are ids.
        self.vote_start = set()
        self.vote_next = set()
        self.vote_stop = set()
        self.day = 0
        self.task_game_loop = None
        self.next_flag.clear()
        self.last_nextcmd_time = time.time()
        self.timer_stopped = True
        self.task_run_timer_phase = None

    def get_last_nextcmd_time(self):
        return self.last_nextcmd_time

    def get_guild(self):
        return self.guild

    def is_started(self):
        return self.game_phase != GamePhase.NEW_GAME

    def awake(self):
        pass

    @staticmethod
    def generate_roles(interface, ids, names_dict):
        ROLE_CONFIG_FILE = "role_config.json"
        try:
            # Load the file everytime to ensure admin can change config while the bot is already running
            with open(ROLE_CONFIG_FILE) as f:
                role_config = json.load(f)
        except:
            # Default config
            print(f"{ROLE_CONFIG_FILE} not found, using default config")
            role_config = [
                    ["Werewolf", "Seer"  , "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Villager", "Lycan"],
                    ["Werewolf", "Guard" , "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Villager", "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Villager", "Villager", "Lycan"],
                    ["Werewolf", "Seer"  , "Villager", "Lycan"   , "Lycan"],
                    ["Werewolf", "Guard" , "Villager", "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Lycan"   , "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Villager", "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Lycan"   , "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Lycan"   , "Lycan"   , "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Villager", "Villager", "Villager"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Villager", "Lycan"   , "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Villager", "Lycan"   , "Lycan"   , "Lycan"],
                    ["Werewolf", "Seer"  , "Guard"   , "Lycan"   , "Lycan"   , "Lycan"   , "Lycan"]
                ]

        ids = list(ids)
        game_role = random.choice([role_list for role_list in role_config if len(role_list)==len(ids)])

        random.shuffle(ids)
        r = {id_: roles.get_role_type(role_name)(interface, id_, names_dict[id_]) for id_,role_name in zip(ids, game_role)}
        print("Player list:", r)
        return r

    async def start(self, init_players=None):
        if self.is_stopped and self.game_phase == GamePhase.NEW_GAME:
            self.game_phase = GamePhase.DAY
            self.is_stopped = False
            self.last_nextcmd_time = time.time()
            await self.interface.send_text_to_channel(text_template.generate_start_text(), config.LOBBY_CHANNEL)
            if not init_players:
                self.players = self.generate_roles(self.interface, list(self.players.keys()), self.playersname)
                # Must use list(dict_keys) in python >= 3.3
            else:
                self.players = init_players

            role_list = dict(Counter(v.__class__.__name__ for v in self.players.values()))

            await self.create_channel()

            await self.interface.send_text_to_channel(text_template.generate_role_list_text(role_list), config.GAMEPLAY_CHANNEL)

            self.start_time = datetime.datetime.now()

            self.task_game_loop = asyncio.create_task(self.run_game_loop(), name="task_game_loop")
            # print(self.task_game_loop)

    async def create_channel(self):
        await asyncio.gather(
            self.interface.create_channel(config.GAMEPLAY_CHANNEL),
            self.interface.create_channel(config.WEREWOLF_CHANNEL),
            self.interface.create_channel(config.CEMETERY_CHANNEL),
            *[player.create_personal_channel() for player in self.players.values()]
        )

    async def stop(self):
        if self.is_stopped: return
        print("======= Game stopped =======")
        self.is_stopped = True
        self.next_flag.clear()
        await self.cancel_running_task(self.task_game_loop)
        await self.cancel_running_task(self.task_run_timer_phase)

        if self.players:
            await self.delete_channel()
        self.reset_game_state()
        await asyncio.sleep(1)
        await self.interface.create_channel(config.GAMEPLAY_CHANNEL)

    async def delete_channel(self):
        try:
            await asyncio.gather(
                self.interface.delete_channel(config.GAMEPLAY_CHANNEL),
                self.interface.delete_channel(config.WEREWOLF_CHANNEL),
                self.interface.delete_channel(config.CEMETERY_CHANNEL),
                *[player.delete_personal_channel() for player in self.players.values()]
            )
        except Exception as e:
            print(e)

    async def add_player(self, id_, player_name):
        if id_ in self.players:
            return -1

        print("Player", id_, "joined")
        self.players[id_] = None
        self.playersname[id_] = player_name
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True)
        await self.interface.send_text_to_channel(f"Chào <@{id_}>", config.GAMEPLAY_CHANNEL)
        return len(self.players)  # Return number of current players

    async def remove_player(self, id_):
        if id_ not in self.players:
            return -1

        print("Player", id_, "left")
        del self.players[id_]
        del self.playersname[id_]
        await self.interface.send_text_to_channel(f"Bye <@{id_}>", config.GAMEPLAY_CHANNEL)
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=False, is_send=False)
        return len(self.players)  # Return number of current players

    def get_alive_players(self):
        return sorted(
            [player for player in self.players.values() if player.is_alive()],
            key=lambda player: player.player_id
        )

    def get_dead_players(self):
        return sorted(
            [player for player in self.players.values() if not player.is_alive()],
            key=lambda player: player.player_id
        )

    def display_alive_player(self):
        return "\n".join((
            "======== Alive players: =======",
            "\n".join(
                map(str, [
                    (player_id, player.__class__.__name__)
                    for player_id, player in self.players.items()
                    if player.is_alive()
                ])
            ),
            "\n"
        ))

    def get_vote_status(self):
        # From {"u1":"u2", "u2":"u1", "u3":"u1"}
        # to {"u2": {"u1"}, "u1": {"u3", "u2"}}
        d = self.voter_dict
        table_dict = reduce(lambda d, k: d.setdefault(k[1], set()).add(k[0]) or d, d.items(), dict())
        print(table_dict)
        return table_dict

    async def run_game_loop(self):
        print("Starting game loop")
        for _id, player in self.players.items():
            if isinstance(player, roles.Werewolf):
                print("Wolf: ", player)
                await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)
                await self.interface.send_text_to_channel(f"Chào sói <@{_id}>", config.WEREWOLF_CHANNEL)
            # else:  # Enable this will not allow anyone to see config.WEREWOLF_CHANNEL including Admin player
            #     await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)

        await asyncio.sleep(0)  # This return CPU to main thread
        print("Started game loop")
        try:
            while not self.is_stopped:
                print("Phase:", self.game_phase)

                # New phase
                await self.new_phase()

                await asyncio.gather(*[role.on_phase(self.game_phase) for role in self.get_alive_players()])

                print("After gather")
                # Wait for `!next` from Admin
                # or Next phase control from bot

                await self.next_flag.wait()  # Blocking wait here
                print("After wait")
                self.next_flag.clear()
                print("After clear")

                await self.end_phase()
                # End_phase

                print("End phase")
                if self.is_end_game():
                    self.is_stopped = True  # Need to update this value in case of end game.
                    break
        except asyncio.CancelledError:
            print("run_game_loop(): cancelled while doing task")
        except Exception as e:
            print("run_game_loop(): stopped while doing task")
            print("Error: ", e)

        if any(a_player.is_alive() for a_player in self.players.values() if isinstance(a_player, roles.Werewolf)):
            await self.interface.send_text_to_channel(text_template.generate_endgame_text("Werewolf"), config.GAMEPLAY_CHANNEL)
        elif any(isinstance(player, roles.Fox) for player in self.players.values() if player.is_alive()):
            await self.interface.send_text_to_channel(text_template.generate_endgame_text("Fox"), config.GAMEPLAY_CHANNEL)
        else:
            await self.interface.send_text_to_channel(text_template.generate_endgame_text("Villager"), config.GAMEPLAY_CHANNEL)
        await asyncio.gather(*[player.on_end_game() for player in self.players.values()])
        # Print werewolf list:
        werewolf_list = ", ".join([str(f"<@{_id}>") for _id, a_player in self.players.items() if isinstance(a_player, roles.Werewolf)])
        await self.interface.send_text_to_channel(f"{werewolf_list} là Sói.", config.GAMEPLAY_CHANNEL)
        await self.cancel_running_task(self.task_run_timer_phase)
        print("End game loop")

    def is_end_game(self):
        num_werewolf = 0
        num_players = 0
        for _, player in self.players.items():
            if player.is_alive():
                num_players += 1
                if isinstance(player, roles.Werewolf):
                    num_werewolf += 1
        print("DEBUG: ", num_players, num_werewolf)
        return num_werewolf == 0 or num_werewolf * 2 >= num_players

    @staticmethod
    def get_top_voted(list_id):
        top_voted = Counter(list_id).most_common(2)
        print("get_top_voted", top_voted)
        if len(top_voted) == 1 or (len(top_voted) == 2 and top_voted[0][1] > top_voted[1][1]):
            return top_voted[0][0], top_voted[0][1]
        return None, 0  # have no vote or equal voted

    async def do_new_daytime_phase(self):
        print("do_new_daytime_phase")
        self.day += 1
        if self.players:
            await self.interface.send_text_to_channel(text_template.generate_day_phase_beginning_text(self.day), config.GAMEPLAY_CHANNEL)
            embed_data = text_template.generate_player_list_embed(self.get_alive_players(), "Alive")
            await self.interface.send_embed_to_channel(embed_data, config.GAMEPLAY_CHANNEL)

    async def do_end_daytime_phase(self):
        print("do_end_daytime_phase")
        if self.voter_dict:
            lynched, votes = Game.get_top_voted(list(self.voter_dict.values()))
            print("lynced list:", self.voter_dict)
            self.voter_dict = {}
            if lynched:
                await self.players[lynched].get_killed()
                await self.interface.send_text_to_channel(text_template.generate_execution_text(f"<@{lynched}>", votes), config.GAMEPLAY_CHANNEL)
            else:
                await self.interface.send_text_to_channel(text_template.generate_execution_text(f"", 0), config.GAMEPLAY_CHANNEL)
        else:
            await self.interface.send_text_to_channel(text_template.generate_execution_text(f"", 0), config.GAMEPLAY_CHANNEL)

    async def do_new_nighttime_phase(self):
        print("do_new_nighttime_phase")
        if self.players:
            await self.interface.send_text_to_channel(
                text_template.generate_night_phase_beginning_text(),
                config.GAMEPLAY_CHANNEL
            )
            await self.interface.send_text_to_channel(
                text_template.generate_before_voting_werewolf(),
                config.WEREWOLF_CHANNEL
            )
            embed_data = text_template.generate_player_list_embed(self.get_alive_players(), "Alive")
            await self.interface.send_embed_to_channel(embed_data, config.WEREWOLF_CHANNEL)
            # Send alive player list to all skilled characters (guard, seer, etc.)
            await asyncio.gather(*[player.on_action(embed_data) for player in self.get_alive_players() if not isinstance(player, roles.Witch)])

            embed_data = text_template.generate_player_list_embed(self.get_dead_players(), "Dead")
            # Send dead player list to Witch if Witch has not used skill
            if embed_data:  # This table can be empty (Noone is dead)
                await asyncio.gather(*[player.on_action(embed_data) for player in self.get_alive_players() if (isinstance(player, roles.Witch) and player.get_power())])


    async def do_end_nighttime_phase(self):
        print("do_end_nighttime_phase")
        kills = None
        if self.wolf_kill_dict:
            killed, _ = Game.get_top_voted(list(self.wolf_kill_dict.values()))
            self.night_pending_kill_list.append(killed)
            self.wolf_kill_dict = {}

        if len(self.night_pending_kill_list):
            final_kill_list = []
            for _id in self.night_pending_kill_list:
                if await self.players[_id].get_killed():  # Guard can protect Fox from Seer kill
                    final_kill_list.append(_id)

            kills = ", ".join([f"<@{_id}>" for _id in final_kill_list])
            self.night_pending_kill_list = []  # Reset killed list for next day

        await self.interface.send_text_to_channel(text_template.generate_killed_text(kills), config.GAMEPLAY_CHANNEL)

        for _id in self.reborn_set:
            await self.players[_id].on_reborn()
        self.reborn_set = set()

    async def new_phase(self):
        self.last_nextcmd_time = time.time()
        print(self.display_alive_player())
        if self.timer_enable:
            await self.cancel_running_task(self.task_run_timer_phase)
            self.task_run_timer_phase = asyncio.create_task(self.run_timer_phase(), name="task_run_timer_phase")

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

    async def cancel_running_task(self, current_task):
        # Cancel running timer phase to prevent multiple task instances
        try:
            print("Cancelling.... ", current_task)
            current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                print("... cancelled now")
            except:
                print("Cancelled task in cancel_running_task")
        except Exception as e:
            print(e)
            print("Task not found")

    async def next_phase_cmd(self):  # This is called from `!next`
        # Cancel running timer phase to prevent multiple task instances
        await self.cancel_running_task(self.task_run_timer_phase)
        await self.next_phase()

    async def next_phase(self):
        print("Next phase")
        asyncio.get_event_loop().call_soon_threadsafe(self.next_flag.set)
        print("Done Next phase flag")

    def set_timer_phase(self, timer_phase_list):
        self.timer_phase = timer_phase_list

    async def run_timer_phase(self):
        print("run_timer_phase")
        try:
            self.timer_stopped = False
            daytime, nighttime, period = self.timer_phase
            timecount = daytime
            if self.game_phase == GamePhase.NIGHT:
                timecount = nighttime

            for count in range(timecount, 0, -1):
                if self.timer_stopped:
                    break
                if count % period == 0 or count <= 5:
                    print(f"{count} remaining")
                    await self.interface.send_text_to_channel(text_template.generate_timer_remaining_text(count), config.GAMEPLAY_CHANNEL)
                await asyncio.sleep(1)
            if not self.timer_stopped:
                print("stop timer")
                await self.interface.send_text_to_channel(text_template.generate_timer_up_text(), config.GAMEPLAY_CHANNEL)
                await self.next_phase()
        except asyncio.CancelledError:
            print("cancel_me(): cancel sleep")
        except:
            print("Unknown run_timer_phase")

    async def do_player_action(self, cmd, author_id, target_id):
        assert self.players is not None
        # print(self.players)
        author = self.players.get(author_id)
        if author is None or not author.is_alive():
            return f"You must be alive ingame to {cmd}!"

        target = self.players.get(target_id)
        if target is None:
            return "Invalid target user. Target user is not a player"

        if not target.is_alive() and cmd!="reborn":
            return text_template.generate_dead_target_text() if cmd=="vote" else text_template.generate_invalid_target()

        if cmd == "vote":
            return await self.vote(author, target)
        elif cmd == "kill":
            return await self.kill(author, target)
        elif cmd == "guard":
            return await self.guard(author, target)
        elif cmd == "seer":
            return await self.seer(author, target)
        elif cmd == "reborn":
            return await self.reborn(author, target)

    async def vote(self, author, target):
        author_id = author.player_id
        target_id = target.player_id

        # Vote for target user
        self.voter_dict[author_id] = target_id
        return text_template.generate_vote_text(f"<@{author_id}>", f"<@{target_id}>")

    async def kill(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_template.generate_invalid_nighttime()

        if not isinstance(author, roles.Werewolf):
            return text_template.generate_invalid_author()

        author_id = author.player_id
        target_id = target.player_id

        self.wolf_kill_dict[author_id] = target_id
        return text_template.generate_kill_text(f"<@{author_id}>", f"<@{target_id}>")

    async def guard(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_template.generate_invalid_nighttime()

        if not isinstance(author, roles.Guard):
            return text_template.generate_invalid_author()

        author_id = author.player_id
        target_id = target.player_id

        if author.get_mana() == 0:
            return text_template.generate_out_of_mana()

        if config.GUARD_PREVENT_SELF_PROTECTION and author_id == target_id:
            return text_template.generate_invalid_guard_selfprotection()
        if author.is_yesterday_target(target_id):
            return text_template.generate_invalid_guard_yesterdaytarget()

        author.on_use_mana()
        author.set_guard_target(target_id)
        target.get_protected()
        return text_template.generate_after_voting_guard(f"<@{target_id}>")

    async def seer(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_template.generate_invalid_nighttime()

        if not isinstance(author, roles.Seer):
            return text_template.generate_invalid_author()

        author_id = author.player_id
        target_id = target.player_id

        if author.get_mana() == 0:
            return text_template.generate_out_of_mana()

        author.on_use_mana()
        if config.SEER_CAN_KILL_FOX and isinstance(target, roles.Fox):
            self.night_pending_kill_list.append(target_id)

        return text_template.generate_after_voting_seer(f"<@{target_id}>", target.seer_seen_as_werewolf())

    async def reborn(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_template.generate_invalid_nighttime()

        if not isinstance(author, roles.Witch):
            return text_template.generate_invalid_author()

        author_id = author.player_id
        target_id = target.player_id

        if author.get_power() == 0:
            return text_template.generate_out_of_power()

        if target.is_alive():
            return text_template.generate_invalid_player_alive(f"<@{target_id}>")

        author.on_use_power()
        self.reborn_set.add(target_id)

        return text_template.generate_after_witch_reborn(f"<@{target_id}>")

    async def test_game(self):
        print("====== Begin test game =====")
        await self.test_case_real_players()  # Will tag real people on Discord
        # await self.test_case_simulated_players() # Better for fast testing. Use with ConsoleInterface only

        print("====== End test game =====")

    async def test_case_real_players(self):
        print("====== Begin test case =====")
        DELAY_TIME = 3
        real_id = dict((i+1, x) for i, x in enumerate(config.DISCORD_TESTING_USERS_ID))
        await self.add_player(real_id[1], "w")
        await self.add_player(real_id[2], "s")
        await self.add_player(real_id[3], "v1")
        await self.add_player(real_id[4], "v2")
        players = {
            real_id[1]: roles.Werewolf(self.interface, real_id[1], "w"),
            real_id[2]: roles.Seer(self.interface,     real_id[2], "s"),
            real_id[3]: roles.Villager(self.interface, real_id[3], "v1"),
            real_id[4]: roles.Villager(self.interface, real_id[4], "v2"),
        }
        await self.start(players)
        print(await self.vote(real_id[1], real_id[2]))
        print(await self.vote(real_id[3], real_id[2]))
        print(await self.vote(real_id[4], real_id[1]))

        await self.next_phase()  # go NIGHT
        time.sleep(DELAY_TIME)
        print(await self.kill(real_id[1], real_id[3]))

        await self.next_phase()  # go DAY
        time.sleep(DELAY_TIME)

        await self.next_phase()
        time.sleep(DELAY_TIME)
        await self.stop()
        time.sleep(DELAY_TIME)
        print("====== End test case =====")


class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list[guild_id]


if __name__ == "__main__":
    game_list = GameList()
