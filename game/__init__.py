# FIXME:
# pylint: disable=too-many-lines
import datetime
import random
import time
import json
import traceback
import asyncio
from collections import Counter, defaultdict
from functools import reduce

import config
import utils
import text_templates
from game import const, roles, text_template, modes
from game.modes.new_moon import NewMoonMode
from game.voting_party import VotingParty


def command_verify_author(valid_role):
    def wrapper(cmd_func):
        async def execute(game, author, *a, **kw):
            if author is not None and not isinstance(author, valid_role):
                return text_templates.generate_text("invalid_author_text")

            return await cmd_func(game, author, *a, **kw)

        return execute

    return wrapper


def command_verify_phase(valid_phase):
    def wrapper(cmd_func):
        async def execute(game, author, *a, **kw):
            if game.game_phase != valid_phase:
                return text_templates.generate_text(
                    "invalid_phase_text",
                    phase=text_templates.get_word_in_language(str(valid_phase))
                )

            return await cmd_func(game, author, *a, **kw)

        return execute

    return wrapper


class Game:
    # FIXME:
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    def __init__(self, guild, interface):
        self.guild = guild  # Should not use. Reserved for future.
        self.interface = interface
        self.channels = [
            config.LOBBY_CHANNEL,
            config.GAMEPLAY_CHANNEL,
            config.LEADERBOARD_CHANNEL,
            config.WEREWOLF_CHANNEL,
            # Personal channel will go into role class
        ]  # List of channels in game
        self.next_flag = asyncio.Event()
        self.timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
        self.timer_enable = True
        self.modes = {}
        self.new_moon_mode = NewMoonMode()
        self.play_time_start = datetime.time(0, 0, 0)  # in UTC
        self.play_time_end = datetime.time(0, 0, 0)  # in UTC
        self.play_zone = "UTC+7"
        self.async_lock = asyncio.Lock()
        self.reset_game_state()  # Init other game variables every end game.

        self.werewolf_party = VotingParty(
            self.interface,
            config.WEREWOLF_CHANNEL,
            "werewolf_welcome_text",
            "werewolf_before_voting_text",
            "werewolf_kill_text",
            "kill_list_title"
        )

    def reset_game_state(self, is_rematching=False):
        print("reset_game_state")
        self.is_stopped = True
        self.start_time = None
        if is_rematching:
            self.players = {player_id: None for player_id in self.players}
        else:
            self.players = {}  # id: Player
            self.playersname = {}  # id: Username
        self.watchers = set()  # Set of id
        self.game_phase = const.GamePhase.NEW_GAME
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
        self.new_moon_mode.set_random_event()
        self.auto_hook = defaultdict(list)
        self.tanner_is_lynched = False

    def get_winner(self):
        if self.winner is None:
            return "None"
        return self.winner.__name__

    def get_last_nextcmd_time(self):
        return self.last_nextcmd_time

    def get_guild(self):
        return self.guild

    def is_started(self):
        return self.game_phase != const.GamePhase.NEW_GAME

    def is_ended(self):
        return self.winner is not None

    def set_mode(self, mode_id, status):
        read_modes = utils.common.read_json_file("json/game_config.json")
        modes_list = list(read_modes.keys())

        if not modes_list:
            return "Mode list not found."
        if not mode_id.isdigit():
            return "Mode ID must be a valid number."
        if int(mode_id) < 1 or int(mode_id) > len(modes_list):
            return f"Mode ID must be between 1 and {len(modes_list)}"
        if status not in ["on", "off"]:
            return "Set mode value must be `on` or `off`"

        mode_str = modes_list[int(mode_id) - 1]
        utils.common.update_json_file("json/game_config.json", mode_str, "True" if status == 'on' else "False")

        if mode_str == "new_moon":
            if status == "on":
                self.new_moon_mode.turn_on()
            else:
                self.new_moon_mode.turn_off()

        elif mode_str == "witch_can_kill":
            roles.Witch.set_can_kill(status=="on")

        status_str = modes.generate_on_off_value(status)

        return text_templates.generate_text("set_mode_successful_text", mode_str=mode_str, status_str=status_str)

    def read_modes(self):
        game_modes = utils.common.read_json_file("json/game_config.json")
        # Read json dict into runtime dict modes
        for k, v in game_modes.items():
            self.modes[k] = v == "True"

        if self.modes.get("new_moon", False):
            self.new_moon_mode.turn_on()
        else:
            self.new_moon_mode.turn_off()

        # Backward compatible
        if "allow_guard_self_protection" not in self.modes and "prevent_guard_self_protection" in self.modes:
            self.modes["allow_guard_self_protection"] = not self.modes["prevent_guard_self_protection"]
            print("prevent_guard_self_protection is deprecated, please use allow_guard_self_protection in config file instead")

        roles.Witch.set_can_kill(self.modes.get("witch_can_kill", False))

    def add_default_roles(self, role_json_in_string):
        try:
            user_roles = json.loads("".join(role_json_in_string))
            if isinstance(user_roles, list) and all(map(lambda x: isinstance(x, dict), user_roles)):
                self.runtime_roles = user_roles
                return "Config loaded."
            return "Invalid json format. Use list of dictionary. Eg in role_config.json"
        except Exception:
            self.runtime_roles = None
            return "Invalid json format."

    def generate_roles(self, interface, ids, names_dict):
        def dict_to_list(cfg, number=0):
            yield from (name for name in cfg for _ in range(cfg[name]))
            yield from ('Werewolf' if i % 4 == 0 else 'Villager' for i in range(number - sum(cfg.values())))

        if self.runtime_roles:
            role_config = self.runtime_roles
        else:
            role_config = utils.common.read_json_file("json/role_config.json")

        ids = list(ids)
        try:
            game_role = random.choice([
                dict_to_list(role_dict)
                for role_dict in role_config if sum(role_dict.values()) == len(ids)
            ])
        except IndexError:
            game_role = dict_to_list(role_config[-1], len(ids))

        random.shuffle(ids)
        if self.modes.get("couple_random"):
            # Replace Cupid by Villager:
            # print("DEBUG----", game_role)
            game_role = map(lambda role: role if role != 'Cupid' else 'Villager', game_role)
            # print("DEBUG----", game_role)

        r = {
            id_: roles.get_role_type(role_name)(interface, id_, names_dict[id_])
            for id_, role_name in zip(ids, game_role)
        }
        print("Player list:", r)
        return r

    def get_role_list(self):
        role_list = dict(Counter(v.__class__.__name__ for v in self.players.values()))
        if not self.modes.get("hidden_role"):
            formatted_roles = ", ".join(f"{role}: {count}" for role, count in role_list.items())
            return text_templates.generate_text("role_list_text", roles_data=formatted_roles)
        return text_templates.generate_text("hidden_role_warning_text")

    def generate_player_list_embed(self, alive_status=None):
        # Handle 3 types of list: All, Alive, Dead
        reveal_role = self.modes.get("reveal_mode", False)
        role_list = []
        if alive_status is True:
            player_list = self.get_alive_players()
            action_name = "alive_player_list_embed"
        elif alive_status is False:
            player_list = self.get_dead_players()
            action_name = "dead_player_list_embed"
        else:
            player_list = self.get_all_players()
            action_name = "all_player_list_embed"
            role_list = [self.get_role_list()]

        if player_list:
            id_player_list = text_template.generate_id_player_list(player_list, alive_status, reveal_role)
            print("generate_player_list_embed", alive_status, reveal_role, player_list, id_player_list)
            embed_data = text_templates.generate_embed(action_name, [id_player_list, role_list])
            return embed_data
        return None

    async def start(self, init_players=None):
        if self.is_stopped and self.game_phase == const.GamePhase.NEW_GAME:
            self.game_phase = const.GamePhase.DAY
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
            await self.interface.send_text_to_channel(
                modes.generate_modes_text({mode: str(value) for mode, value in self.modes.items()}),
                config.GAMEPLAY_CHANNEL
            )

            if not self.modes.get("hidden_role"):
                await self.interface.send_text_to_channel(self.get_role_list(), config.GAMEPLAY_CHANNEL)

            self.start_time = datetime.datetime.now()

            self.task_game_loop = asyncio.create_task(self.run_game_loop(), name="task_game_loop")
            # print(self.task_game_loop)

    async def create_channel(self):
        await asyncio.gather(
            self.interface.create_channel(config.GAMEPLAY_CHANNEL),
            self.werewolf_party.create_channel(),
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

    async def rematch(self, rematch_player_id):
        print("======= Game rematched =======")
        if self.is_stopped:
            return

        self.next_flag.clear()
        await self.cancel_running_task(self.task_game_loop)
        await self.cancel_running_task(self.task_run_timer_phase)

        if self.players:
            await self.delete_channel()

        current_players = ", ".join(f"<@{_id}>" for _id in self.players)
        rematch_data = text_templates.generate_embed(
            "rematch_embed",
            [
                [current_players]
            ],
            rematch_player_id=rematch_player_id,
            total_players=len(self.players)
        )
        await self.interface.send_embed_to_channel(rematch_data, config.LOBBY_CHANNEL)

        self.reset_game_state(True)
        await self.interface.create_channel(config.GAMEPLAY_CHANNEL)
        # Add current players to Gameplay
        await asyncio.gather(
            *[self.interface.add_user_to_channel(_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True) for _id in self.players]
        )
        await self.interface.send_action_text_to_channel("gameplay_welcome_rematch_text", config.GAMEPLAY_CHANNEL, rematch_players=current_players)
        await asyncio.sleep(0)

    async def delete_channel(self):
        try:
            await asyncio.gather(
                self.interface.delete_channel(config.GAMEPLAY_CHANNEL),
                self.werewolf_party.delete_channel(),
                self.interface.delete_channel(config.CEMETERY_CHANNEL),
                self.interface.delete_channel(config.COUPLE_CHANNEL),
                *[player.delete_personal_channel() for player in self.players.values()]
            )
        except Exception as e:
            print(e)

    async def self_check_channel(self):
        try:
            await asyncio.gather(
                *[player.create_personal_channel(self_check=True) for player in self.players.values()]
            )
            return text_templates.generate_text('self_check_text')
        except Exception as e:
            print(e)

    async def add_player(self, id_, player_name):
        async with self.async_lock:
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

    def get_all_players(self):
        return self.get_alive_players() + self.get_dead_players()

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

    def get_following_players_set(self, player_set, cupid_dict):
        return set(cupid_dict[_id] for _id in player_set if _id in cupid_dict)

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

    def get_game_status_description(self):
        if self.is_ended():
            return text_templates.generate_text("end_text")

        if self.game_phase == const.GamePhase.NEW_GAME:
            return text_templates.get_label_in_language("new_game_phase_status")

        if self.is_in_play_time():
            return text_templates.get_label_in_language(
                f"in_playing_time_{'paused' if self.timer_stopped else 'playing'}_status"
            )

        return text_templates.get_label_in_language("out_of_playing_time_status")

    def get_channel_vote_table(self, author_id, channel_name):
        vote_table = None
        table_title = ""

        if self.is_ended():
            return vote_table, table_title

        if self.game_phase == const.GamePhase.NEW_GAME:
            status_table_headers = text_templates.generate_table_headers("game_status_new_game_phase_table_headers")
            vote_table = {
                header: [*value]
                for header, value in zip(status_table_headers, [self.players.keys(), self.watchers, self.vote_start])
            }
            table_title = text_templates.get_label_in_language("waiting_list_title")

        elif self.game_phase == const.GamePhase.DAY:
            vote_table = {f'<@{k}>': v for k, v in self.get_vote_status().items()}
            table_title = text_templates.get_label_in_language("vote_list_title")

        elif self.game_phase == const.GamePhase.NIGHT:
            author = self.players.get(author_id)
            if not author:
                pass

            elif author.is_alive():
                is_personal_channel = channel_name.startswith(config.PERSONAL)

                if isinstance(author, roles.Werewolf) and (channel_name == config.WEREWOLF_CHANNEL or is_personal_channel):
                    vote_table, table_title = self.werewolf_party.get_vote_table_with_title()
            else:
                # TODO: future features in #cemetery channel
                pass

        return vote_table, table_title

    def get_author_status(self, author_id, channel_name):
        author_status = ""

        author = self.players.get(author_id)
        if self.is_ended() or not author:
            return author_status

        is_channel_for_author = channel_name.startswith(config.PERSONAL)
        if self.game_phase == const.GamePhase.NIGHT and is_channel_for_author:
            if author.is_alive():
                if isinstance(author, (roles.Seer, roles.Guard)):
                    author_status = text_templates.get_label_in_language(
                        f"author_{'not_use' if author.get_target() is None else 'used'}_mana_status"
                    )
                elif isinstance(author, (roles.Zombie, roles.Cupid)):
                    author_status = text_templates.get_label_in_language(
                        f"author_{'not_use' if author.get_power() > 0 else 'used'}_power_status"
                    )
                elif isinstance(author, roles.Witch):
                    author_status = text_templates.get_label_in_language(
                        f"author_{'not_use' if author.get_reborn_power() > 0 else 'used'}_reborn_power_status"
                    ) + "\n"
                    author_status += text_templates.get_label_in_language(
                        f"author_{'not_use' if author.get_curse_power() > 0 else 'used'}_curse_power_status"
                    )
                elif not isinstance(author, roles.Werewolf):
                    author_status = text_templates.get_label_in_language("author_sleeping_status")
            else:
                # TODO: future features in #cemetery channel
                author_status = text_templates.get_label_in_language("author_dead_status")

        return author_status

    def get_timer_remaining_time(self):
        if not self.is_ended() and self.game_phase != const.GamePhase.NEW_GAME:
            return self.timecounter

        return None

    def get_vote_status(self, voter_dict=None):
        # From {"u1":"u2", "u2":"u1", "u3":"u1"}
        # to {"u2": {"u1"}, "u1": {"u3", "u2"}}
        if voter_dict is None:
            voter_dict = self.voter_dict

        table_dict = reduce(lambda d, k: d.setdefault(k[1], set()).add(k[0]) or d, voter_dict.items(), {})
        print(table_dict)
        return table_dict

    async def show_status(self, author, channel_name):
        status_description = self.get_game_status_description()

        if self.is_ended():
            await self.interface.send_text_to_channel(status_description, channel_name)
            return

        passed_days = str(self.day) if self.day > 0 else ""
        remaining_time = self.get_timer_remaining_time()
        vote_table, table_title = self.get_channel_vote_table(author.id, channel_name)
        author_status = self.get_author_status(author.id, channel_name)

        print(
            status_description, passed_days, remaining_time, vote_table,
            text_template.generate_vote_field(vote_table), table_title, author_status
        )
        status_embed_data = text_templates.generate_embed(
            "game_status_with_table_embed",
            [
                [passed_days],
                [text_template.generate_timer_remaining_text(remaining_time)],
                text_template.generate_vote_field(vote_table),
                [author_status]
            ],
            status_description=status_description,
            phase_str=text_templates.get_word_in_language(str(self.game_phase)),
            table_title=table_title
        )
        await self.interface.send_embed_to_channel(status_embed_data, channel_name)

        if self.is_started():
            players_embed_data = self.generate_player_list_embed()
            await self.interface.send_embed_to_channel(players_embed_data, channel_name)

    async def run_game_loop(self):
        print("Starting game loop")
        self.prev_playtime = self.is_in_play_time()
        for _id, player in self.players.items():
            if isinstance(player, roles.Werewolf):
                print("Wolf: ", player)
                await self.werewolf_party.add_player(_id)
                await self.werewolf_party.send_welcome_text(_id)
            # else:  # Enable this will not allow anyone to see config.WEREWOLF_CHANNEL including Admin player
            #     await self.interface.add_user_to_channel(_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)

        embed_data = self.generate_player_list_embed(True)
        await asyncio.gather(*[role.on_start_game(embed_data) for role in self.get_alive_players()])

        info = text_templates.generate_text(
            "werewolf_list_text", werewolf_str=", ".join(f"<@{_id}>" for _id in self.werewolf_party.get_all_players())
        )
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
        couple_reveal_text = "\n\n" + "💘 " + " x ".join(f"<@{player_id}>" for player_id in self.cupid_dict) if self.cupid_dict else ""
        await self.interface.send_text_to_channel(
            "\n".join(text_template.generate_reveal_str_list(reveal_list, game_winner, self.cupid_dict)) + couple_reveal_text,
            config.GAMEPLAY_CHANNEL
        )

        # write to leaderboard
        if self.start_time is not None:  # game has been started
            game_result = text_templates.generate_embed(
                "game_result_embed",
                [
                    [str(self.day)],
                    # \u00A0\u00A0 is one space character for discord embed
                    # Put \u200B\n at first of the next field to break line
                    [f"🎉\u00A0\u00A0\u00A0\u00A0{game_winner}\u00A0\u00A0\u00A0\u00A0🎉"],
                    text_template.generate_reveal_str_list(reveal_list, game_winner, self.cupid_dict),
                    [" x ".join(f"<@{player_id}>" for player_id in self.cupid_dict)] if self.cupid_dict else []
                ],
                start_time_str=self.start_time.strftime(text_templates.get_format_string("datetime"))
            )
            await self.interface.send_embed_to_channel(game_result, config.LEADERBOARD_CHANNEL)

        await self.cancel_running_task(self.task_run_timer_phase)
        print("End game loop")

    def get_winning_role(self):
        alives = self.get_alive_players()
        num_players = len(alives)
        num_werewolf = sum(isinstance(p, roles.Werewolf) for p in alives)

        print("DEBUG: ", num_players, num_werewolf)

        # Check Tanner
        if self.tanner_is_lynched:
            return roles.Tanner

        # Check end game
        if num_werewolf != 0 and num_werewolf * 2 < num_players:
            return None

        # Check Cupid
        couple = [self.players[i] for i in self.cupid_dict]
        if num_players == 2 and \
                any(isinstance(p, roles.Werewolf) for p in couple) and \
                any(not isinstance(p, roles.Werewolf) for p in couple) and \
                all(p in alives for p in couple):
            return roles.Cupid

        # Werewolf still alive then werewolf win
        if num_werewolf != 0:
            return roles.Werewolf

        # Werewolf died and fox still alive
        if any(isinstance(p, roles.Fox) for p in alives):
            return roles.Fox

        return roles.Villager

    def get_voted_list(self, voter_dict):
        # self.voter_dict = {}  # Dict of voter:voted players {user1:user2, user3:user4, user2:user1}. All items are ids.
        voted_list = []
        for voter, voted in voter_dict.items():
            voted_list.append(voted)
            if isinstance(self.players[voter], roles.Chief):
                voted_list.append(voted)
        return voted_list

    async def control_muting_party_channel(self, channel_name, is_muted, player_check_func=None):
        """
        Mute/Unmute all alive players in party channel (e.g. GAMEPLAY_CHANNEL, WEREWOLF_CHANNEL, COUPLE_CHANNEL)
        """
        await asyncio.gather(*[
            self.interface.add_user_to_channel(_id, channel_name, is_read=True, is_send=not is_muted)
            for _id, player in self.players.items()
            if player.is_alive() and (player_check_func is None or player_check_func(player))
        ])

    async def announce_current_new_moon_event(self):
        if self.modes.get("new_moon", False):
            await self.interface.send_action_text_to_channel(
                f"new_moon_{'special' if self.new_moon_mode.has_special_event() else 'no'}_event_text",
                config.GAMEPLAY_CHANNEL,
                event_name=self.new_moon_mode.get_current_event_name(),
                event_description=self.new_moon_mode.get_current_event_description()
            )

    async def do_new_daytime_phase(self):
        print("do_new_daytime_phase")
        self.day += 1
        if self.players:
            await self.interface.send_action_text_to_channel("day_phase_beginning_text", config.GAMEPLAY_CHANNEL, day=self.day)
            embed_data = self.generate_player_list_embed()
            await self.interface.send_embed_to_channel(embed_data, config.GAMEPLAY_CHANNEL)

            self.new_moon_mode.set_random_event()
            await self.announce_current_new_moon_event()

            if self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.PUNISHMENT and len(self.get_dead_players()):
                alive_players_embed_data = self.generate_player_list_embed(True)
                await self.new_moon_mode.do_new_daytime_phase(self.interface, alive_players_embed_data=alive_players_embed_data)

            # Mute all party channels
            # Unmute all alive players in config.GAMEPLAY_CHANNEL
            await self.control_muting_party_channel(config.WEREWOLF_CHANNEL, True, lambda player: isinstance(player, roles.Werewolf))
            await self.control_muting_party_channel(config.COUPLE_CHANNEL, True, lambda player: player.player_id in self.cupid_dict)
            await self.control_muting_party_channel(config.GAMEPLAY_CHANNEL, False)
        else:
            print("Error no player in game.")
            await self.stop()

    async def do_end_daytime_phase(self):
        # FIXME:
        # pylint: disable=too-many-branches
        await self.do_run_auto_hook()
        print("do_end_daytime_phase")
        lynched, votes = None, 0
        if self.voter_dict:
            lynched, votes = VotingParty.get_top_voted(self.get_voted_list(self.voter_dict))
            print("lynched list:", self.voter_dict)
            self.voter_dict = {}

        if self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.HEADS_OR_TAILS:
            coin_toss_value = self.new_moon_mode.do_coin_toss()
            print("coin toss value =", coin_toss_value)
            if coin_toss_value != 0:
                lynched, votes = None, 0

            await self.new_moon_mode.do_action(self.interface, coin_toss_value=coin_toss_value)

        if lynched:
            await self.players[lynched].get_killed()
            await self.interface.send_action_text_to_channel(
                "execution_player_text", config.GAMEPLAY_CHANNEL,
                voted_user=f"<@{lynched}>", highest_vote_number=votes
            )

            if isinstance(self.players[lynched], roles.Tanner):
                self.tanner_is_lynched = True

            cupid_couple = self.cupid_dict.get(lynched)
            if cupid_couple is not None:
                await self.players[cupid_couple].get_killed(True)
                await self.interface.send_action_text_to_channel(
                    "couple_died_on_day_text", config.GAMEPLAY_CHANNEL,
                    died_player=f"<@{lynched}>", follow_player=f"<@{cupid_couple}>"
                )
                # Kill anyone who is hunted if hunter dies with his couple
                hunted = await self.get_hunted_target_on_hunter_death(cupid_couple)
                if hunted:
                    await self.interface.send_action_text_to_channel(
                        "hunter_killed_text", config.GAMEPLAY_CHANNEL, target=f"<@{hunted}>"
                    )
            hunted = await self.get_hunted_target_on_hunter_death(lynched)
            if hunted:
                await self.interface.send_action_text_to_channel(
                    "hunter_killed_text", config.GAMEPLAY_CHANNEL, target=f"<@{hunted}>"
                )
        else:
            await self.interface.send_action_text_to_channel("execution_none_text", config.GAMEPLAY_CHANNEL)

        players_embed_data = self.generate_player_list_embed()
        await self.interface.send_embed_to_channel(players_embed_data, config.GAMEPLAY_CHANNEL)

        await self.announce_current_new_moon_event()

        # Unmute all party channels
        # Mute all players in config.GAMEPLAY_CHANNEL
        await self.control_muting_party_channel(config.WEREWOLF_CHANNEL, False, lambda player: isinstance(player, roles.Werewolf))
        await self.control_muting_party_channel(config.COUPLE_CHANNEL, False, lambda player: player.player_id in self.cupid_dict)
        await self.control_muting_party_channel(config.GAMEPLAY_CHANNEL, True)

    async def do_new_nighttime_phase(self):
        print("do_new_nighttime_phase")
        if self.players:
            await self.interface.send_action_text_to_channel(
                "night_phase_beginning_text",
                config.GAMEPLAY_CHANNEL
            )
            alive_embed_data = self.generate_player_list_embed(True)
            dead_embed_data = self.generate_player_list_embed(False)

            await self.werewolf_party.do_new_voting_phase(alive_embed_data)
            await asyncio.gather(*[
                player.on_night_start(alive_embed_data, dead_embed_data) for player in self.get_all_players()
            ])

    async def do_end_nighttime_phase(self):
        # FIXME:
        # pylint: disable=too-many-branches
        await self.do_run_auto_hook()
        print("do_end_nighttime_phase")

        # TODO: move to Player class
        for player in self.get_alive_players():
            if isinstance(player, roles.Seer):
                await self.seer_do_end_nighttime_phase(player)
            elif isinstance(player, roles.Guard):
                await self.guard_do_end_nighttime_phase(player)
            elif isinstance(player, roles.Witch):
                await self.witch_do_end_nighttime_phase(player)

        kills = None
        killed, _ = self.werewolf_party.get_party_top_voted()
        if killed:
            self.night_pending_kill_list.append(killed)

        self.werewolf_party.do_end_voting_phase()

        cupid_couple = None
        if self.night_pending_kill_list:
            final_kill_set = set()
            for _id in self.night_pending_kill_list:
                if await self.players[_id].get_killed():  # Guard can protect Fox from Seer kill
                    final_kill_set.add(_id)
                    hunted = await self.get_hunted_target_on_hunter_death(_id)
                    if hunted:  # Hunter hunted one in couple
                        final_kill_set.add(hunted)
                        if self.cupid_dict.get(hunted):
                            cupid_couple = self.cupid_dict[hunted]
                            final_kill_set.add(cupid_couple)

                    if self.cupid_dict.get(_id):
                        cupid_couple = self.cupid_dict[_id]  # Hunter is one in couple
                        hunted = await self.get_hunted_target_on_hunter_death(cupid_couple)
                        if hunted:
                            final_kill_set.add(hunted)

            kills = ", ".join(f"<@{_id}>" for _id in final_kill_set)
            self.night_pending_kill_list = []  # Reset killed list for next day

        # Morning deaths announcement
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

        if self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.TWIN_FLAME and self.cupid_dict:
            await self.new_moon_mode.do_end_nighttime_phase(self.interface)
            self.reborn_set.update(self.get_following_players_set(self.reborn_set, self.cupid_dict))

        for _id in self.reborn_set:
            await self.players[_id].on_reborn()

        self.reborn_set = set()

    async def guard_do_end_nighttime_phase(self, author):
        target_id = author.get_target()
        if target_id is None:
            return

        target = self.players[target_id]
        target.get_protected()

        await author.send_to_personal_channel(
            text_templates.generate_text("guard_result_text", target=f"<@{target_id}>")
        )

    async def seer_do_end_nighttime_phase(self, author):
        target_id = author.get_target()
        if target_id is None:
            return

        target = self.players[target_id]

        if self.modes.get("seer_can_kill_fox") and isinstance(target, roles.Fox):
            self.night_pending_kill_list.append(target_id)

        if self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.SOMNAMBULISM:
            await self.new_moon_mode.do_action(self.interface, target=target)

        await author.send_to_personal_channel(
            text_templates.generate_text(
                f"seer_result_{'' if target.seer_seen_as_werewolf() else 'not_'}werewolf_text",
                target=f"<@{target_id}>"
            )
        )

    async def witch_do_end_nighttime_phase(self, author):
        reborn_target_id = author.get_reborn_target()
        if author.get_reborn_power() > 0 and reborn_target_id:
            author.on_use_reborn_power()
            self.reborn_set.add(reborn_target_id)

            await author.send_to_personal_channel(
                text_templates.generate_text("witch_reborn_result_text", target=f"<@{reborn_target_id}>")
            )

        if roles.Witch.is_can_kill():
            curse_target_id = author.get_curse_target()
            if author.get_curse_power() > 0 and curse_target_id:
                author.on_use_curse_power()
                self.night_pending_kill_list.append(curse_target_id)

                await author.send_to_personal_channel(
                    text_templates.generate_text("witch_curse_result_text", target=f"<@{curse_target_id}>")
                )

    async def new_phase(self):
        self.last_nextcmd_time = time.time()
        print(self.display_alive_player())
        if self.timer_enable:
            await self.cancel_running_task(self.task_run_timer_phase)
            self.task_run_timer_phase = asyncio.create_task(self.run_timer_phase(), name="task_run_timer_phase")

        if self.game_phase == const.GamePhase.DAY:
            await self.do_new_daytime_phase()
        elif self.game_phase == const.GamePhase.NIGHT:
            await self.do_new_nighttime_phase()

    async def end_phase(self):
        assert self.game_phase != const.GamePhase.NEW_GAME
        if self.game_phase == const.GamePhase.DAY:
            await self.do_end_daytime_phase()
        elif self.game_phase == const.GamePhase.NIGHT:
            await self.do_end_nighttime_phase()

        if self.game_phase == const.GamePhase.DAY:
            self.game_phase = const.GamePhase.NIGHT
        elif self.game_phase == const.GamePhase.NIGHT:
            self.game_phase = const.GamePhase.DAY
        else:
            print("Incorrect game flow")

    async def cancel_running_task(self, current_task):
        # Cancel running timer phase to prevent multiple task instances
        try:
            print("Cancelling....", current_task)
            current_task.cancel()
            try:
                await current_task
            except asyncio.CancelledError:
                print("... cancelled now")
            except Exception as e:
                print(e)
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
            if self.game_phase == const.GamePhase.NIGHT:
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
        except Exception as e:
            print(e)
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
        if self.play_time_start > self.play_time_end:
            return self.play_time_start <= time_point or time_point <= self.play_time_end

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

    async def do_new_moon_event_action(self):
        if not self.modes.get("new_moon", False):
            return None

        # TODO
        return None

    async def do_player_action(self, cmd, author_id, *targets_id):
        # FIXME
        # pylint: disable=too-many-return-statements, too-many-branches
        assert self.players is not None
        # print(self.players)
        author = self.players.get(author_id)
        if author is None:
            return text_templates.generate_text("invalid_author_text")

        is_alive_author_command = cmd not in ["zombie", "punish"]
        if is_alive_author_command != author.is_alive():
            return text_templates.generate_text(
                "invalid_author_status_text",
                status=text_templates.get_word_in_language("alive" if is_alive_author_command else "dead")
            )

        if cmd == "auto":
            return await self.register_auto(author, *targets_id)

        targets = []
        for target_id in targets_id:
            target = self.players.get(target_id)
            if target is None:
                return text_templates.generate_text("invalid_target_text")
            targets.append(target)

        if cmd == "zombie":
            return await self.zombie(author)

        is_alive_target_command = cmd != "reborn"
        if is_alive_target_command != targets[0].is_alive():
            return text_templates.generate_text(
                "invalid_target_status_text",
                status=text_templates.get_word_in_language("alive" if is_alive_target_command else "dead")
            )

        if cmd in ("vote", "punish", "kill", "guard", "hunter", "seer", "reborn", "curse"):
            return await getattr(self, cmd)(author, targets[0])

        if cmd == "ship":
            if self.modes.get("couple_random"):
                return text_templates.generate_text("invalid_ship_with_random_couple_text")
            return await self.ship(author, targets[0], targets[1])

        return text_template.generate_invalid_command_text(cmd)

    async def vote(self, author, target):
        author_id = author.player_id
        target_id = target.player_id
        if author_id == target_id:
            return text_templates.generate_text("prevent_self_voting_text")

        # Vote for target user
        self.voter_dict[author_id] = target_id
        return text_templates.generate_text("vote_text", author=f"<@{author_id}>", target=f"<@{target_id}>")

    async def punish(self, author, target):
        new_moon_punishment_event = self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.PUNISHMENT
        is_day_time = self.game_phase == const.GamePhase.DAY
        # May also check if author is dead or not?
        if not (new_moon_punishment_event and is_day_time):
            return text_templates.generate_text("invalid_punish_in_cemetery_text")

        author_id = author.player_id
        target_id = target.player_id

        # Punish for target user
        self.voter_dict[author_id] = target_id

        return await self.new_moon_mode.do_action(self.interface, author=f"<@{author_id}>", target=f"<@{target_id}>")

    @command_verify_author(roles.Werewolf)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def kill(self, author, target):
        if self.modes.get("new_moon", False) and self.new_moon_mode.current_event == NewMoonMode.FULL_MOON_VEGETARIAN:
            return await self.new_moon_mode.do_action(self.interface)

        author_id = author.player_id
        target_id = target.player_id

        return self.werewolf_party.register_vote(author_id, target_id)

    @command_verify_author(roles.Guard)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def guard(self, author, target):
        roles.Guard.set_allow_self_protection(self.modes.get("allow_guard_self_protection", False))
        return author.register_target(target.player_id)

    @command_verify_author(roles.Seer)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def seer(self, author, target):
        return author.register_target(target.player_id)

    @command_verify_author(roles.Witch)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def reborn(self, author, target):
        return author.register_reborn_target(target.player_id)

    @command_verify_author(roles.Witch)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def curse(self, author, target):
        return author.register_curse_target(target.player_id)

    @command_verify_author(roles.Zombie)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def zombie(self, author):
        author_id = author.player_id

        if author.get_power() == 0:
            return text_templates.generate_text("out_of_power_text")

        author.on_use_power()
        self.reborn_set.add(author_id)

        return text_templates.generate_text("zombie_after_reborn_text")

    @command_verify_author(roles.Cupid)
    async def ship(self, author, target1, target2):
        if author is not None:  # quick adapt couple_random enable
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

    @command_verify_author(roles.Hunter)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def hunter(self, author, target):
        return author.register_target(target.player_id)

    async def get_hunted_target_on_hunter_death(self, hunter):
        """Kill anyone who is hunted"""
        if isinstance(self.players[hunter], roles.Hunter):
            hunted = self.players[hunter].get_target()
            if hunted and hunted != hunter:
                if await self.players[hunted].get_killed():
                    return hunted
        return None

    async def register_auto(self, author, subcmd):
        def check(pred):
            def wrapper(f):
                async def execute(*a, **kw):
                    if pred():
                        print("Check success")
                        return await f(*a, **kw)
                    print("Check failed")
                return execute
            return wrapper

        def is_night():
            return self.game_phase == const.GamePhase.NIGHT

        def is_day():
            return self.game_phase == const.GamePhase.DAY

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
                while target.player_id in self.cupid_dict:
                    target = random.choice(self.get_alive_players())
            msg = await self.seer(author, target)
            await self.interface.send_text_to_channel("[Auto] " + msg, author.channel_name)

        if subcmd == "off":
            self.auto_hook[author] = []
            return "Clear auto successed"

        if subcmd == "seer":
            if has_role(roles.Seer)():
                self.auto_hook[author].append(auto_seer)
                return "Register auto seer success"
            return "You are not a seer"

        if subcmd == "guard":
            if has_role(roles.Guard)():
                self.auto_hook[author].append(auto_guard)
                return "Register auto guard success"
            return "You are not a guard"

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
        delay_time = 3
        real_id = dict((i, x) for i, x in enumerate(config.DISCORD_TESTING_USERS_ID, 1))
        await self.add_player(real_id[1], "w")
        await self.add_player(real_id[2], "s")
        await self.add_player(real_id[3], "v1")
        await self.add_player(real_id[4], "v2")
        players = {
            real_id[1]: roles.Werewolf(self.interface, real_id[1], "w"),
            real_id[2]: roles.Seer(self.interface, real_id[2], "s"),
            real_id[3]: roles.Villager(self.interface, real_id[3], "v1"),
            real_id[4]: roles.Villager(self.interface, real_id[4], "v2"),
        }
        await self.start(players)
        print(await self.vote(real_id[1], real_id[2]))
        print(await self.vote(real_id[3], real_id[2]))
        print(await self.vote(real_id[4], real_id[1]))

        await self.next_phase()  # go NIGHT
        time.sleep(delay_time)
        print(await self.kill(real_id[1], real_id[3]))

        await self.next_phase()  # go DAY
        time.sleep(delay_time)

        await self.next_phase()
        time.sleep(delay_time)
        await self.stop()
        time.sleep(delay_time)
        print("====== End test case =====")


class GameList:
    def __init__(self):
        self.game_list = {}

    def add_game(self, guild_id, game):
        self.game_list[guild_id] = game

    def get_game(self, guild_id):
        return self.game_list.get(guild_id, None)


if __name__ == "__main__":
    game_list = GameList()
