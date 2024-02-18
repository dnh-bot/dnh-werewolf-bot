import config
from game import roles, text_template
import text_templates

import utils
import datetime
import random
import time
import json
from enum import Enum
from collections import Counter, defaultdict
from functools import reduce
import traceback
import asyncio
import tzlocal

from game.roles import create_from_str


class GamePhase(Enum):
    NEW_GAME = 0
    DAY = 1
    NIGHT = 2

    def __str__(self):
        return self.name.lower() + "_phase"


class Game:
    def __init__(self, guild, interface):
        self.guild = guild  # Should not use. Reserved for future.
        self.interface = interface
        self.channels = [
            config.LOBBY_CHANNEL,
            config.GAMEPLAY_CHANNEL,
            config.LEADERBOARD_CHANNEL,
            config.WEREWOLF_CHANNEL,
            # Personal channel will goes into role class
        ]  # List of channels in game
        self.next_flag = asyncio.Event()
        self.timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
        self.timer_enable = True
        self.modes = {}
        self.play_time_start = datetime.time(0, 0, 0)  # in UTC
        self.play_time_end = datetime.time(0, 0, 0)  # in UTC
        self.play_zone = "UTC+7"
        self.reset_game_state()  # Init other game variables every end game.
        if self.load_saved_game_state():
            self.timer_enable = False
            print("successfully load saved game state")

    def reset_game_state(self):
        print("reset_game_state")
        self.is_stopped = True
        self.start_time = None
        self.players = {}  # id: Player
        self.playersname = {}  # id: username
        self.watchers = set()  # set of id
        self.game_phase = GamePhase.NEW_GAME
        self.wolf_kill_dict = {}  # dict[wolf] -> player
        self.reborn_set = set()
        self.cupid_dict = {}  # dict[player1] -> player2, dict[player2] -> player1
        self.night_pending_kill_list = []
        self.voter_dict = {}  # Dict of voted players {user1:user2, user3:user4, user2:user1}. All items are ids.
        self.vote_start = set()
        self.vote_next = set()
        self.vote_stop = set()
        self.day = 0
        self.timecounter = 0
        self.task_game_loop = None
        self.next_flag.clear()
        self.last_nextcmd_time = time.time()
        self.timer_stopped = True
        self.task_run_timer_phase = None
        self.winner = None
        self.runtime_roles = None
        self.prev_playtime = self.is_in_play_time()
        self.auto_hook = defaultdict(list)

    def save_game_state(self):
        game_state = {}

        if not self.is_ended():
            game_state["players"] = [repr(p) for p in self.players.values()]
            game_state["watchers"] = list(self.watchers)
            game_state["game_phase"] = self.game_phase.value
            game_state["timer_phase"] = self.timer_phase
            game_state["phase_time_left"] = self.timecounter
            game_state["day"] = self.day
            game_state["couple"] = list(self.cupid_dict.keys())
            game_state["vote_start"] = list(self.vote_start)
            game_state["vote_next"] = list(self.vote_next)
            game_state["vote_stop"] = list(self.vote_stop)

            game_state["phase_command_targets"] = {
                "vote": self.voter_dict,
                "kill": self.wolf_kill_dict
            }

        try:
            with open("saved_game.json", "w", encoding="utf8") as f:
                json.dump(game_state, f, indent=4)
                print(f"successfully saved game into saved_game.json")
                return True
        except Exception as e:
            print("update saved_game.json failed.", e)
            return False

    def load_saved_game_state(self):
        # TODO: apply this function to somewhere
        game_state = utils.common.read_json_file("saved_game.json")
        if game_state:
            self.players = {}
            self.playersname = {}
            for player_str in game_state["players"]:
                player = create_from_str(self.interface, player_str)
                self.players[player.player_id] = player
                self.playersname[player.player_id] = player.player_name

            self.watchers = set(game_state["watchers"])
            self.game_phase = GamePhase(game_state["game_phase"])
            self.timer_phase = game_state["timer_phase"]
            self.timecounter = game_state["phase_time_left"]
            self.day = game_state["day"]
            if game_state["couple"]:
                self.cupid_dict = dict([tuple(game_state["couple"]), tuple(game_state["couple"][::-1])])
            self.vote_start = set(game_state["vote_start"])
            self.vote_next = set(game_state["vote_next"])
            self.vote_stop = set(game_state["vote_stop"])
            self.voter_dict = game_state["phase_command_targets"]["vote"]
            self.wolf_kill_dict = game_state["phase_command_targets"]["kill"]

            return True  # TODO: restore to 'return True'

        return False

    def get_winner(self):
        if self.winner is None:
            return "None"
        return self.winner.__name__

    def get_last_nextcmd_time(self):
        return self.last_nextcmd_time

    def get_guild(self):
        return self.guild

    def is_started(self):
        return self.game_phase != GamePhase.NEW_GAME

    def is_ended(self):
        return self.winner is not None

    def set_mode(self, mode_str, on):
        utils.common.update_json_file("json/game_config.json", mode_str, "True" if on else "False")
        return f"Set mode '{mode_str}' is {on}. Warning: This setting is permanent!"

    def read_modes(self):
        modes = utils.common.read_json_file("json/game_config.json")
        # Read json dict into runtime dict modes
        for k, v in modes.items():
            if v == "True":
                self.modes[k] = True

    def add_default_roles(self, role_json_in_string):
        try:
            user_roles = json.loads("".join(role_json_in_string))
            if isinstance(user_roles, list) and all(map(lambda x: isinstance(x, dict), user_roles)):
                self.runtime_roles = user_roles
                return f"Config loaded."
            return f"Invalid json format. Use list of dictionary. Eg in role_config.json"
        except:
            self.runtime_roles = None
            return f"Invalid json format."

    def generate_roles(self, interface, ids, names_dict):
        def dict_to_list(config, number=0):
            yield from (name for name in config for _ in range(config[name]))
            yield from ('Werewolf' if i % 4 == 0 else 'Villager' for i in range(number-sum(config.values())))

        if self.runtime_roles:
            role_config = self.runtime_roles
        else:
            role_config = utils.common.read_json_file("json/role_config.json")

        ids = list(ids)
        try:
            game_role = random.choice([dict_to_list(role_dict)
                                      for role_dict in role_config if sum(role_dict.values()) == len(ids)])
        except IndexError:
            game_role = dict_to_list(role_config[-1], len(ids))

        random.shuffle(ids)
        if self.modes.get("couple_random"):
            # Replace Cupid by Villager:
            # print("DEBUG----", game_role)
            game_role = map(lambda role: role if role != 'Cupid' else 'Villager', game_role)
            # print("DEBUG----", game_role)

        r = {id_: roles.get_role_type(role_name)(
            interface, id_, names_dict[id_]) for id_, role_name in zip(ids, game_role)}
        print("Player list:", r)
        return r

    def get_role_list(self):
        role_list = dict(Counter(v.__class__.__name__ for v in self.players.values()))
        if not self.modes.get("hidden_role"):
            return text_templates.generate_text("role_list_text", roles_data=role_list)
        return "Warning: hidden_role is ON. Cannot show list"

    async def start(self, init_players=None):
        if self.is_stopped and self.game_phase == GamePhase.NEW_GAME:
            self.game_phase = GamePhase.DAY
            self.is_stopped = False
            self.last_nextcmd_time = time.time()
            self.read_modes()  # Read json config mode into runtime dict
            await self.interface.send_action_text_to_channel("start_text", config.LOBBY_CHANNEL)
            if not init_players:
                self.players = self.generate_roles(self.interface, list(self.players.keys()), self.playersname)
                # Must use list(dict_keys) in python >= 3.3
            else:
                self.players = init_players



            await self.create_channel()
            await self.interface.send_text_to_channel(text_template.generate_modes(dict(zip(self.modes, map(lambda x: "True", self.modes.values())))), config.GAMEPLAY_CHANNEL)

            if not self.modes.get("hidden_role"):
                await self.interface.send_text_to_channel(self.get_role_list(), config.GAMEPLAY_CHANNEL)

            self.start_time = datetime.datetime.now()

            self.task_game_loop = asyncio.create_task(self.run_game_loop(), name="task_game_loop")
            # print(self.task_game_loop)

    async def create_channel(self):
        await asyncio.gather(
            self.interface.create_channel(config.GAMEPLAY_CHANNEL),
            self.interface.create_channel(config.WEREWOLF_CHANNEL),
            self.interface.create_channel(config.CEMETERY_CHANNEL),
            self.interface.create_channel(config.COUPLE_CHANNEL)
        )
        await asyncio.gather(
            *[player.create_personal_channel() for player in self.players.values()]
        )

    async def stop(self):
        print("======= Game stopped =======")
        if self.is_stopped:
            return

        self.next_flag.clear()
        await self.cancel_running_task(self.task_game_loop)
        await self.cancel_running_task(self.task_run_timer_phase)

        if self.players:
            await self.delete_channel()
        self.reset_game_state()
        await self.interface.send_action_text_to_channel("end_text", config.LOBBY_CHANNEL)
        await self.interface.create_channel(config.GAMEPLAY_CHANNEL)
        await asyncio.sleep(0)

    async def delete_channel(self):
        try:
            await asyncio.gather(
                self.interface.delete_channel(config.GAMEPLAY_CHANNEL),
                self.interface.delete_channel(config.WEREWOLF_CHANNEL),
                self.interface.delete_channel(config.CEMETERY_CHANNEL),
                self.interface.delete_channel(config.COUPLE_CHANNEL),
                *[player.delete_personal_channel() for player in self.players.values()]
            )
        except Exception as e:
            print("delete_channel", traceback.format_exc())

    async def add_player(self, id_, player_name):
        if id_ in self.players:
            return -1

        if id_ in self.watchers:
            print("Player", id_, "unwatched and joined")
            self.watchers.remove(id_)
        else:
            print("Player", id_, "joined")

        self.players[id_] = None
        self.playersname[id_] = player_name
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True)
        await self.interface.send_action_text_to_channel("gameplay_join_text", config.GAMEPLAY_CHANNEL, player_id=id_)
        return len(self.players)  # Return number of current players

    async def remove_player(self, id_):
        if id_ not in self.players:
            return -1

        print("Player", id_, "left")
        del self.players[id_]
        del self.playersname[id_]
        await self.interface.send_action_text_to_channel("gameplay_leave_text", config.GAMEPLAY_CHANNEL, player_id=id_)
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
                    for player_id, player in self.players.items() if player.is_alive()
                ])
            ),
            "\n"
        ))

    async def add_watcher(self, id_):
        if id_ in self.players:
            return -2
        if id_ in self.watchers:
            return -1

        print("Watcher", id_, "watched")
        self.watchers.add(id_)
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False)
        await self.interface.send_action_text_to_channel("gameplay_watch_text", config.GAMEPLAY_CHANNEL, player_id=id_)
        return len(self.watchers)  # Return number of current watchers

    async def remove_watcher(self, id_):
        if id_ in self.players:
            return -2
        if id_ not in self.watchers:
            return -1

        print("Watcher", id_, "unwatched")
        self.watchers.remove(id_)
        await self.interface.send_action_text_to_channel("gameplay_unwatch_text", config.GAMEPLAY_CHANNEL, player_id=id_)
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=False, is_send=False)
        return len(self.watchers)  # Return number of current watchers

    def get_game_status(self, channel_name, author_id):
        """
        Returns:
        game status description,
        a phase's remaining time,
        vote table (if any) with its description,
        author status.
        """
        status_description = ""
        remaining_time = None
        vote_table = None
        table_title = ""
        author_status = ""

        if self.is_ended() or not isinstance(self.game_phase, GamePhase):
            return status_description, remaining_time, vote_table, table_title, author_status

        if self.game_phase == GamePhase.NEW_GAME:
            status_description = text_templates.get_label_in_language("new_game_phase_status")
            status_table_headers = text_templates.generate_table_headers("game_status_new_game_phase_table_headers")
            vote_table = {
                header: [*value]
                for header, value in zip(status_table_headers, [self.players.keys(), self.watchers, self.vote_start])
            }
            table_title = text_templates.get_label_in_language("waiting_list_title")
        else:
            remaining_time = self.timecounter

            if self.is_in_play_time():
                if self.timer_stopped:
                    status_description = text_templates.get_label_in_language("in_playing_time_paused_status")
                else:
                    status_description = text_templates.get_label_in_language("in_playing_time_playing_status")
            else:
                status_description = text_templates.get_label_in_language("out_of_playing_time_status")

        if self.game_phase == GamePhase.DAY:
            vote_table = {f'<@!{k}>': v for k, v in self.get_vote_status().items()}
            table_title = text_templates.get_label_in_language("vote_list_title")

        elif self.game_phase == GamePhase.NIGHT:
            author = self.players.get(author_id)
            if not author:
                author_status = "Chưa có gì để xem đâu :>"

            elif author.is_alive():
                if isinstance(author, roles.Werewolf) and (channel_name == config.WEREWOLF_CHANNEL or channel_name.startswith("personal")):
                    vote_table = {f'<@!{k}>': v for k, v in self.get_vote_status(self.wolf_kill_dict).items()}
                    table_title = text_templates.get_label_in_language("kill_list_title")

                elif isinstance(author, (roles.Seer, roles.Guard)) and channel_name.startswith("personal"):
                    if author.get_mana() > 0:
                        author_status = text_templates.get_label_in_language("author_not_use_mana_status")
                    else:
                        author_status = text_templates.get_label_in_language("author_used_mana_status")

                elif isinstance(author, (roles.Zombie, roles.Cupid)) and channel_name.startswith("personal"):
                    if author.get_power() > 0:
                        author_status = text_templates.get_label_in_language("author_not_use_power_status")
                    else:
                        author_status = text_templates.get_label_in_language("author_used_power_status")

                else:
                    author_status = text_templates.get_label_in_language("author_sleeping_status")
            else:
                # TODO: future features in #cemetery channel
                author_status = text_templates.get_label_in_language("author_dead_status")

        return status_description, remaining_time, vote_table, table_title, author_status

    def get_vote_status(self, voter_dict=None):
        # From {"u1":"u2", "u2":"u1", "u3":"u1"}
        # to {"u2": {"u1"}, "u1": {"u3", "u2"}}
        if voter_dict is None:
            voter_dict = self.voter_dict

        table_dict = reduce(lambda d, k: d.setdefault(k[1], set()).add(k[0]) or d, voter_dict.items(), dict())
        print(table_dict)
        return table_dict

    async def run_game_loop(self):
        print("Starting game loop")
        self.prev_playtime = self.is_in_play_time()
        werewolf_list = []
        for _id, player in self.players.items():
            if isinstance(player, roles.Werewolf):
                print("Wolf: ", player)
                await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)
                await self.interface.send_action_text_to_channel("werewolf_welcome_text", config.WEREWOLF_CHANNEL, user=f"<@{_id}>")
                werewolf_list.append(_id)
            # else:  # Enable this will not allow anyone to see config.WEREWOLF_CHANNEL including Admin player
            #     await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)

        embed_data = text_template.generate_player_list_embed(self.get_alive_players(), alive_status=True)
        await asyncio.gather(*[role.on_start_game(embed_data) for role in self.get_alive_players()])

        info = text_templates.generate_text("werewolf_list_text", werewolf_str=", ".join(f"<@{_id}>" for _id in werewolf_list))
        print("werewolf_list_text", info)
        await asyncio.gather(*[role.on_betrayer(info) for role in self.get_alive_players() if isinstance(role, roles.Betrayer)])

        await self.interface.send_text_to_channel(text_template.generate_play_time_text(self.play_time_start, self.play_time_end, self.play_zone), config.GAMEPLAY_CHANNEL)

        if self.modes.get("couple_random"):
            random_cupid_couple = random.sample(self.get_alive_players(), 2)
            await self.ship(None, *random_cupid_couple)

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
                self.save_game_state()
                # End_phase

                print("End phase")

                winner = self.get_winning_role()
                if winner is not None:
                    self.winner = winner
                    break
        except asyncio.CancelledError:
            print("run_game_loop(): cancelled while doing task")
        except Exception as e:
            print("run_game_loop(): stopped while doing task")
            print("Error: ", e)
            print(traceback.format_exc())

        game_winner = self.get_winner()
        await self.interface.send_action_text_to_channel("endgame_text", config.GAMEPLAY_CHANNEL, winner=game_winner)
        await asyncio.gather(*[player.on_end_game() for player in self.players.values()])

        reveal_list = [(_id, player.__class__.__name__) for _id, player in self.players.items()]
        await self.interface.send_text_to_channel(
            "\n".join(text_template.generate_reveal_str_list(reveal_list)), config.GAMEPLAY_CHANNEL
        )

        # write to leaderboard
        if self.start_time is not None:  # game has been started
            game_result = text_templates.generate_embed(
                "game_result_embed",
                [
                    [str(self.day)],
                    [game_winner],
                    text_template.generate_reveal_str_list(reveal_list),
                    [" x ".join(f"<@{player_id}>" for player_id in self.cupid_dict.keys())] if self.cupid_dict else []
                ],
                start_time_str=self.start_time.strftime(text_templates.get_format_string("datetime"))
            )
            await self.interface.send_embed_to_channel(game_result, config.LEADERBOARD_CHANNEL)

        await self.cancel_running_task(self.task_run_timer_phase)
        print("End game loop")

    def get_winning_role(self):
        alives = self.get_alive_players()
        num_players = len(alives)
        num_werewolf = sum([isinstance(p, roles.Werewolf) for p in alives])

        print("DEBUG: ", num_players, num_werewolf)

        # check end game
        if num_werewolf != 0 and num_werewolf * 2 < num_players:
            return None

        # check cupid
        couple = [self.players[i] for i in self.cupid_dict.keys()]
        if num_players == 2 and \
           any([isinstance(p, roles.Werewolf) for p in couple]) and \
           any([not isinstance(p, roles.Werewolf) for p in couple]) and \
           all([c in alives for c in couple]):
            return roles.Cupid

        # werewolf still alive then werewolf win
        if num_werewolf != 0:
            return roles.Werewolf

        # werewolf died and fox still alive
        if any([isinstance(p, roles.Fox) for p in alives]):
            return roles.Fox

        return roles.Villager

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
            await self.interface.send_action_text_to_channel("day_phase_beginning_text", config.GAMEPLAY_CHANNEL, day=self.day)
            embed_data = text_template.generate_player_list_embed(self.get_alive_players(), alive_status=True)
            await self.interface.send_embed_to_channel(embed_data, config.GAMEPLAY_CHANNEL)

            # Unmute all alive players in config.GAMEPLAY_CHANNEL
            await asyncio.gather(
                *[self.interface.add_user_to_channel(_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True)
                  for _id, player in self.players.items() if player.is_alive()]
            )
        else:
            print("Error no player in game.")
            await self.stop()

    async def do_end_daytime_phase(self):
        await self.do_run_auto_hook()
        print("do_end_daytime_phase")
        if self.voter_dict:
            lynched, votes = Game.get_top_voted(list(self.voter_dict.values()))
            print("lynched list:", self.voter_dict)
            self.voter_dict = {}
            if lynched:
                await self.players[lynched].get_killed()
                await self.interface.send_action_text_to_channel(
                    "execution_player_text", config.GAMEPLAY_CHANNEL,
                    voted_user=f"<@{lynched}>", highest_vote_number=votes
                )

                cupid_couple = self.cupid_dict.get(lynched)
                if cupid_couple is not None:
                    await self.players[cupid_couple].get_killed(True)
                    await self.interface.send_action_text_to_channel(
                        "couple_died_on_day_text", config.GAMEPLAY_CHANNEL,
                        died_player=f"<@{lynched}>", follow_player=f"<@{cupid_couple}>"
                    )
            else:
                await self.interface.send_action_text_to_channel("execution_none_text", config.GAMEPLAY_CHANNEL)
        else:
            await self.interface.send_action_text_to_channel("execution_none_text", config.GAMEPLAY_CHANNEL)

        # Mute all players in config.GAMEPLAY_CHANNEL
        await asyncio.gather(
            *[self.interface.add_user_to_channel(_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False)
                for _id, player in self.players.items() if player.is_alive()]
        )

    async def do_new_nighttime_phase(self):
        print("do_new_nighttime_phase")
        if self.players:
            await self.interface.send_action_text_to_channel(
                "night_phase_beginning_text",
                config.GAMEPLAY_CHANNEL
            )
            await self.interface.send_action_text_to_channel(
                "werewolf_before_voting_text",
                config.WEREWOLF_CHANNEL
            )
            embed_data = text_template.generate_player_list_embed(self.get_alive_players(), alive_status=True)
            await self.interface.send_embed_to_channel(embed_data, config.WEREWOLF_CHANNEL)
            # Send alive player list to all skilled characters (guard, seer, etc.)
            if self.modes.get("witch_can_kill"):
                await asyncio.gather(*[player.on_action(embed_data) for player in self.get_alive_players()])
            else:
                await asyncio.gather(*[player.on_action(embed_data) for player in self.get_alive_players() if not isinstance(player, roles.Witch)])

            embed_data = text_template.generate_player_list_embed(self.get_dead_players(), alive_status=False)
            # Send dead player list to Witch if Witch has not used skill
            if embed_data:  # This table can be empty (No one is dead)
                await asyncio.gather(*[player.on_action(embed_data) for player in self.get_alive_players() if isinstance(player, roles.Witch) and player.get_power()])

    async def do_end_nighttime_phase(self):
        await self.do_run_auto_hook()
        print("do_end_nighttime_phase")
        kills = None
        if self.wolf_kill_dict:
            killed, _ = Game.get_top_voted(list(self.wolf_kill_dict.values()))
            if killed:
                self.night_pending_kill_list.append(killed)
            self.wolf_kill_dict = {}

        cupid_couple = None
        if len(self.night_pending_kill_list):
            final_kill_list = []
            for _id in self.night_pending_kill_list:
                if await self.players[_id].get_killed():  # Guard can protect Fox from Seer kill
                    final_kill_list.append(_id)
                    if self.cupid_dict.get(_id):
                        cupid_couple = self.cupid_dict[_id]

            kills = ", ".join(f"<@{_id}>" for _id in final_kill_list)
            self.night_pending_kill_list = []  # Reset killed list for next day

        await self.interface.send_action_text_to_channel(
            "killed_users_text" if kills else "killed_none_text", config.GAMEPLAY_CHANNEL,
            user=kills
        )

        if cupid_couple is not None:
            await self.players[cupid_couple].get_killed(True)
            await self.interface.send_action_text_to_channel(
                "couple_died_on_night_text", config.GAMEPLAY_CHANNEL,
                died_player=f"<@{self.cupid_dict[cupid_couple]}>", follow_player=f"<@{cupid_couple}>"
            )

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
            print("Cancelling....", current_task)
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
        self.vote_next = set()  # Reset to prevent accumulating next through phases
        asyncio.get_event_loop().call_soon_threadsafe(self.next_flag.set)
        print("Done Next phase flag")

    def set_timer_phase(self, timer_phase_list):
        self.timer_phase = timer_phase_list

    async def run_timer_phase(self):
        print("run_timer_phase")
        try:
            self.timer_stopped = False
            daytime, nighttime, period = self.timer_phase
            self.timecounter = daytime
            if self.game_phase == GamePhase.NIGHT:
                self.timecounter = nighttime

            while self.timecounter > 0:
                await self.do_process_with_play_time()

                if not self.timer_stopped and self.is_in_play_time():
                    if self.timecounter % period == 0 or self.timecounter <= 5:
                        print(f"{self.timecounter} remaining")
                        await self.interface.send_action_text_to_channel(
                            "timer_alert_text", config.GAMEPLAY_CHANNEL,
                            timer_remaining_text=text_template.generate_timer_remaining_text(self.timecounter)
                        )
                    self.timecounter -= 1
                await asyncio.sleep(1)

            if not self.timer_stopped:
                print("stop timer")
                await self.interface.send_action_text_to_channel("timer_up_text", config.GAMEPLAY_CHANNEL)
                await self.next_phase()
        except asyncio.CancelledError:
            print("cancel_me(): cancel sleep")
        except:
            print("Unknown run_timer_phase")

    def set_play_time(self, time_start: datetime.time, time_end: datetime.time, zone):
        """
        Set play time range for a game.
        Params:
            time_start: time in UTC
            time_end: time in UTC
        """
        if isinstance(time_start, datetime.time) and isinstance(time_end, datetime.time):
            self.play_time_start = time_start
            self.play_time_end = time_end
            self.play_zone = zone
        else:
            print("Invalid time_start or time_end format", time_start, time_end)

    def is_in_play_time(self):
        time_point = datetime.datetime.utcnow().time()

        if self.play_time_start < self.play_time_end:
            return self.play_time_start <= time_point <= self.play_time_end
        elif self.play_time_start > self.play_time_end:
            return self.play_time_start <= time_point or time_point <= self.play_time_end
        else:
            return True  # a day

    async def do_process_with_play_time(self):
        self.curr_playtime = self.is_in_play_time()
        if self.curr_playtime != self.prev_playtime:
            self.prev_playtime = self.curr_playtime
            await self.interface.send_action_text_to_channel(
                "play_time_in_range_alert_text" if self.curr_playtime else "play_time_out_range_alert_text",
                config.GAMEPLAY_CHANNEL,
                text_day=text_templates.get_word_in_language(str(self.game_phase)),
                timer_remaining_text=text_template.generate_timer_remaining_text(self.timecounter)
            )

    async def do_player_action(self, cmd, author_id, *targets_id):
        assert self.players is not None
        # print(self.players)
        author = self.players.get(author_id)
        if author is None or not author.is_alive():
            if cmd != "zombie":  # Zombie can use skill after death
                return text_templates.generate_text("invalid_alive_author_text", cmd=cmd)

        if cmd == "auto":
            return await self.register_auto(author, *targets_id)


        targets = []
        for target_id in targets_id:
            target = self.players.get(target_id)
            if target is None:
                return text_templates.generate_text("invalid_target_text")
            targets.append(target)

        if cmd != "zombie" and not targets[0].is_alive() and cmd != "reborn":
            return text_templates.generate_text("dead_target_text" if cmd == "vote" else "invalid_target_text")

        if cmd == "vote":
            return await self.vote(author, targets[0])
        elif cmd == "kill":
            return await self.kill(author, targets[0])
        elif cmd == "guard":
            return await self.guard(author, targets[0])
        elif cmd == "seer":
            return await self.seer(author, targets[0])
        elif cmd == "reborn":
            return await self.reborn(author, targets[0])
        elif cmd == "curse":
            return await self.curse(author, targets[0])
        elif cmd == "zombie":
            return await self.zombie(author)
        elif cmd == "ship":
            if self.modes.get("couple_random"):
                return text_templates.generate_text("invalid_ship_with_random_couple_text")
            else:
                return await self.ship(author, *targets[:2])

    async def vote(self, author, target):
        author_id = author.player_id
        target_id = target.player_id

        # Vote for target user
        self.voter_dict[author_id] = target_id
        return text_templates.generate_text("vote_text", author=f"<@{author_id}>", target=f"<@{target_id}>")

    async def kill(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Werewolf):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id
        target_id = target.player_id

        self.wolf_kill_dict[author_id] = target_id
        return text_templates.generate_text("werewolf_kill_text", werewolf=f"<@{author_id}>", target=f"<@{target_id}>")

    async def guard(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Guard):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id
        target_id = target.player_id

        if author.get_mana() == 0:
            return text_templates.generate_text("out_of_mana_text")

        if self.modes.get("prevent_guard_self_protection") and author_id == target_id:
            return text_templates.generate_text("invalid_guard_selfprotection_text")
        if author.is_yesterday_target(target_id):
            return text_templates.generate_text("invalid_guard_yesterdaytarget_text")

        author.on_use_mana()
        author.set_guard_target(target_id)
        target.get_protected()
        return text_templates.generate_text("guard_after_voting_text", target=f"<@{target_id}>")

    async def seer(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Seer):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id
        target_id = target.player_id

        if author.get_mana() == 0:
            return text_templates.generate_text("out_of_mana_text")

        author.on_use_mana()
        if self.modes.get("seer_can_kill_fox") and isinstance(target, roles.Fox):
            self.night_pending_kill_list.append(target_id)

        return text_templates.generate_text(
            f"seer_after_voting_{'' if target.seer_seen_as_werewolf() else 'not_'}werewolf_text",
            target=f"<@{target_id}>"
        )

    async def reborn(self, author, target):
        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Witch):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id
        target_id = target.player_id

        if author.get_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        if target.is_alive():
            return text_templates.generate_text("invalid_player_alive_text", user=f"<@{target_id}>")

        author.on_use_power()
        self.reborn_set.add(target_id)

        return text_templates.generate_text("witch_after_reborn_text", target=f"<@{target_id}>")

    async def curse(self, author, target):
        if not self.modes.get("witch_can_kill"):
            return text_templates.generate_text("mode_disabled_text")

        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Witch):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id
        target_id = target.player_id

        if author.get_curse_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        author.on_use_curse_power()
        # Kill someone
        self.night_pending_kill_list.append(target_id)

        return text_templates.generate_text("witch_after_curse_text", target=f"<@{target_id}>")

    async def zombie(self, author):
        if self.game_phase != GamePhase.NIGHT:
            return text_templates.generate_text("invalid_nighttime_text")

        if not isinstance(author, roles.Zombie):
            return text_templates.generate_text("invalid_author_text")

        author_id = author.player_id

        if author.get_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        author.on_use_power()
        self.reborn_set.add(author_id)

        return text_templates.generate_text("zombie_after_reborn_text")

    async def ship(self, author, target1, target2):
        if author is not None:  # quick adapt couple_random enable
            if not isinstance(author, roles.Cupid):
                return text_templates.generate_text("invalid_author_text")

            if author.get_power() == 0:
                return text_templates.generate_text("out_of_power_text")

            author.on_use_power()

        target1_id = target1.player_id
        target2_id = target2.player_id

        self.cupid_dict[target1_id] = target2_id
        self.cupid_dict[target2_id] = target1_id

        await self.interface.send_action_text_to_channel(
            "couple_shipped_with_text",
            self.players[target1_id].channel_name, target=f"<@{target2_id}> {target2.__class__.__name__}"
        )
        await self.interface.send_action_text_to_channel(
            "couple_shipped_with_text",
            self.players[target2_id].channel_name, target=f"<@{target1_id}> {target1.__class__.__name__}"
        )
        await self.interface.create_channel(config.COUPLE_CHANNEL)
        await self.interface.add_user_to_channel(target1_id, config.COUPLE_CHANNEL, is_read=True, is_send=True)
        await self.interface.add_user_to_channel(target2_id, config.COUPLE_CHANNEL, is_read=True, is_send=True)
        await self.interface.send_action_text_to_channel("couple_welcome_text", config.COUPLE_CHANNEL, user1=f"<@{target1_id}>", user2=f"<@{target2_id}>")

        return text_templates.generate_text("cupid_after_ship_text", target1=f"<@{target1_id}>", target2=f"<@{target2_id}>")

    async def register_auto(self, author, subcmd):
        def check(pred):
            def wrapper(f):
                async def execute(*a, **kw):
                    if pred():
                        print("Check success")
                        return await f(*a, **kw)
                    else:
                        print("Check failed")
                return execute
            return wrapper

        def is_night():
            return self.game_phase == GamePhase.NIGHT

        def is_day():
            return self.game_phase == GamePhase.DAY

        def has_role(role):
            return lambda: isinstance(author, role)

        def is_alive():
            return author.is_alive()

        @check(is_alive)
        @check(is_night)
        @check(has_role(roles.Guard))
        async def auto_guard():
            target = random.choice(self.get_alive_players())
            msg = await self.guard(author, target)
            await self.interface.send_text_to_channel("[Auto] " + msg, author.channel_name)

        @check(is_alive)
        @check(is_night)
        @check(has_role(roles.Seer))
        async def auto_seer():
            target = random.choice(self.get_alive_players())
            if author.player_id in self.cupid_dict:
                while target.player_id in  self.cupid_dict:
                    target = random.choice(self.get_alive_players())
            msg = await self.seer(author, target)
            await self.interface.send_text_to_channel("[Auto] " + msg, author.channel_name)

        if subcmd == "off":
            self.auto_hook[author] = []
            return "Clear auto successed"
        elif subcmd == "seer":
            if has_role(roles.Seer)():
                self.auto_hook[author].append(auto_seer)
                return "Register auto seer success"
            else:
                return "You are not a seer"
        elif subcmd == "guard":
            if has_role(roles.Guard)():
                self.auto_hook[author].append(auto_guard)
                return "Register auto guard success"
            else:
                return "You are not a guard"
        else:
            return "Unknown auto command, please try again"

    async def do_run_auto_hook(self):
        print("do_run_auto_hook")
        await asyncio.gather(*[f() for k in self.auto_hook for f in self.auto_hook[k]])

    async def test_game(self):
        print("====== Begin test game =====")
        await self.test_case_real_players()  # Will tag real people on Discord
        # await self.test_case_simulated_players() # Better for fast testing. Use with ConsoleInterface only

        print("====== End test game =====")

    async def test_case_real_players(self):
        print("====== Begin test case =====")
        DELAY_TIME = 3
        real_id = dict((i, x) for i, x in enumerate(config.DISCORD_TESTING_USERS_ID, 1))
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
