# FIXME:
# pylint: disable=too-many-lines, unidiomatic-typecheck
import datetime
import queue
import random
import time
import json
import traceback
import asyncio
from collections import Counter, defaultdict
from functools import reduce

import config
from database import Database
import utils
import text_templates
from game import const, roles, text_template, modes, generate_roles
from game.modes.new_moon import NewMoonMode
from game.modes.new_moon.events import *


def command_verify_author(valid_role):
    def wrapper(cmd_func):
        async def execute(game, author, *a, **kw):
            if author is not None:
                if not isinstance(author, valid_role):
                    return text_templates.generate_text("invalid_author_text")

                if author.is_action_disabled_today():
                    return text_templates.generate_text("invalid_author_disabled_action_text")

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
        self.__is_on_phase = False
        self.async_lock = asyncio.Lock()
        self.reset_game_state()  # Init other game variables every end game.
        self.database = Database().create_instance()

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
        self.formatted_roles = ""
        self.is_werewolf_diseased = False
        self.wolf_kill_dict = {}  # dict[wolf] -> player
        self.reborn_set = set()
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
        mode_on = status == "on"
        utils.common.update_json_file("json/game_config.json", mode_str, "True" if mode_on else "False")

        if mode_str == "new_moon":
            if mode_on:
                self.new_moon_mode.turn_on()
            else:
                self.new_moon_mode.turn_off()

        elif mode_str == "witch_can_kill":
            roles.Witch.set_can_kill(mode_on)
        elif mode_str == "allow_guard_self_protection":
            roles.Guard.set_allow_self_protection(mode_on)
        elif mode_str == "seer_can_kill_fox":
            roles.Seer.set_can_kill_fox(mode_on)

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
        roles.Guard.set_allow_self_protection(self.modes.get("allow_guard_self_protection", False))
        roles.Seer.set_can_kill_fox(self.modes.get("seer_can_kill_fox", False))

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
        if self.runtime_roles:
            role_config = self.runtime_roles[0]
        else:
            # Use fixed configuration file:
            # role_config = utils.common.read_json_file("json/role_config.json")

            # Use dynamic score system:
            role_config = generate_roles.generate_roles_new_strategy(ids)

        ids = list(ids)
        game_role = utils.common.dict_to_list(role_config)

        # Somehow python dict retain adding order
        # So the Werewolf role will always at the beginning of the dict
        # Shuffle to make the Werewolf role appear randomly
        game_role = list(game_role)
        random.shuffle(game_role)
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
        player_role_list = dict(Counter(v.get_role() for v in self.players.values()))
        if not self.modes.get("hidden_role"):
            roles_text_list = list((f"{role}: {count}" for role, count in player_role_list.items()))
            # To make sure player roles and display roles are not in the same order
            random.shuffle(roles_text_list)
            formatted_roles = ", ".join(roles_text_list)
            return text_templates.generate_text("role_list_text", roles_data=formatted_roles)
        return text_templates.generate_text("hidden_role_warning_text")

    def generate_player_list_embed(self, alive_status=None):
        # Handle 3 types of list: All, Alive, Dead
        reveal_role = self.modes.get("reveal_role", False)
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
            role_list = [self.formatted_roles]

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

            self.formatted_roles = self.get_role_list()

            await self.create_channel()
            await self.interface.send_text_to_channel(
                modes.generate_modes_text({mode: str(value) for mode, value in self.modes.items()}),
                config.GAMEPLAY_CHANNEL
            )

            if not self.modes.get("hidden_role"):
                await self.interface.send_text_to_channel(self.formatted_roles, config.GAMEPLAY_CHANNEL)

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
                self.interface.delete_channel(config.WEREWOLF_CHANNEL),
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
        if id_ in self.vote_start:
            self.vote_start.remove(id_)
        await self.interface.send_action_text_to_channel("gameplay_leave_text", config.GAMEPLAY_CHANNEL, player_id=id_)
        await self.interface.add_user_to_channel(id_, config.GAMEPLAY_CHANNEL, is_read=False, is_send=False)
        return len(self.players)  # Return number of current players

    def get_all_players(self):
        return self.get_alive_players() + self.get_dead_players()

    def get_alive_players(self):
        return [player for player in self.players.values() if player.is_alive()]

    def get_dead_players(self):
        return [player for player in self.players.values() if not player.is_alive()]

    def display_alive_player(self):
        return "\n".join((
            "======== Alive players: =======",
            "\n".join(
                map(str, [
                    (player_id, player.get_role())
                    for player_id, player in self.players.items() if player.is_alive()
                ])
            ),
            "\n"
        ))

    async def get_final_status_changes_with_reasons(self, pending_list):
        """
        Get final status changes with reasons set after a phase.
        pending_list format: [(player_id, reason),...]
        """
        # collect all dead reasons of a player to final_dict
        # format: final_dict = {player_id: [dead_reason,...], ...}
        final_dict = defaultdict(list)
        pending_queue = queue.Queue()
        for info in pending_list:
            pending_queue.put(info)

        while not pending_queue.empty():
            player_id, reason = pending_queue.get()
            status_changed_successfully = False
            if isinstance(reason, const.DeadReason):
                status_changed_successfully = await self.players[player_id].get_killed(reason is const.DeadReason.COUPLE)
            elif isinstance(reason, const.RebornReason):
                status_changed_successfully = await self.players[player_id].on_reborn()

            if status_changed_successfully:
                final_dict[player_id].append(reason)

                for following_info in self.get_following_players(player_id, reason):
                    pending_queue.put(following_info)

        print("final_dict = dict(", *final_dict.items(), ")")

        # convert final_dict to a new dict of player_id list, filter by reason
        # list_by_reason format: {reason: [player_id,...], ...}
        list_by_reason = defaultdict(list)
        for player_id, reason_list in final_dict.items():
            if any(reason is const.DeadReason.HIDDEN for reason in reason_list):  # hidden reason
                list_by_reason[const.DeadReason.HIDDEN].append(player_id)
            elif any(reason is const.RebornReason.HIDDEN for reason in reason_list):  # hidden reason
                list_by_reason[const.RebornReason.HIDDEN].append(player_id)
            else:
                for reason in reason_list:
                    list_by_reason[reason].append(player_id)

        return list_by_reason

    def get_following_players(self, player_id, reason):
        """
        Get following dead/reborn players by followed relation (e.g. hunter, couple,...)
        """
        player = self.players[player_id]
        following_players = []

        if isinstance(player, roles.Hunter) and isinstance(reason, const.DeadReason):
            hunted = player.get_target()
            if hunted and hunted != player_id:
                following_players.append((hunted, const.DeadReason.HUNTED))

        follower_id = player.get_lover()
        if follower_id is not None and not reason.is_couple_following():
            # prevent repeatedly call a couple
            if isinstance(reason, const.DeadReason):
                following_players.append((follower_id, const.DeadReason.COUPLE))

            elif isinstance(reason, const.RebornReason):
                if self.new_moon_mode.get_current_event() is TwinFlame:
                    following_players.append((follower_id, const.RebornReason.COUPLE))

        return following_players

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
                    vote_table = {f'<@{k}>': v for k, v in self.get_vote_status(self.wolf_kill_dict).items()}
                    table_title = text_templates.get_label_in_language("kill_list_title")
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
                [get_event_name(self.new_moon_mode.get_current_event())] if self.new_moon_mode.is_on else [],
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

    def generate_victory_list(self, game_winner):
        victory_list = []
        for player_id, player in self.players.items():
            role, party = player.get_role(), player.get_party()
            party_victory = party == game_winner
            # Cupid is in Villager team. Win with either couple or Villager
            cupid_victory = game_winner == 'Cupid' and (player.get_lover() is not None or role == 'Cupid')
            # Change party roles
            change_party_victory = isinstance(player, roles.Tanner) and party == game_winner

            victory = party_victory or cupid_victory or change_party_victory

            victory_list.append((player_id, role, victory))

        return victory_list

    async def handle_end_game_score_list(self, game_winner, victory_list):
        try:
            player_scores_data = await self.database.read("player_score_list.json")

            for player_id, _, victory in victory_list:
                if victory:
                    player_scores_data[str(player_id)] = int(player_scores_data.get(str(player_id), 0)) + config.RANKING_SCORE_RATE.get("win", 10)
                elif game_winner != 'None':
                    player_scores_data[str(player_id)] = int(player_scores_data.get(str(player_id), 0)) - config.RANKING_SCORE_RATE.get("lose", 2)

            print("End Game Scores: ", player_scores_data)
            await self.database.update("player_score_list.json", player_scores_data)
        except Exception as e:
            print("Error in handle_end_game_score_list: ", e)

    async def show_player_score_list(self, channel_name):
        try:
            player_score_data = await self.database.read("player_score_list.json")
            if not player_score_data:
                return
            score_list_embed = text_template.generate_player_score_list_embed(player_score_data)
            await self.interface.send_embed_to_channel(score_list_embed, channel_name)
        except Exception as e:
            print("Error in show_player_score_list: ", e)

    async def run_game_loop(self):
        print("Starting game loop")
        self.prev_playtime = self.is_in_play_time()
        werewolf_list = self.get_werewolf_list()
        print("Wolf:", werewolf_list)

        embed_data = self.generate_player_list_embed(True)
        werewolf_info = text_templates.generate_text(
            "werewolf_list_text", werewolf_str=", ".join(f"<@{_id}>" for _id in werewolf_list)
        )
        print("werewolf_list_text", werewolf_info)
        await asyncio.gather(*[role.on_start_game(embed_data, werewolf_info) for role in self.get_alive_players()])

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

        victory_list = self.generate_victory_list(game_winner)
        reveal_str_list = text_template.generate_reveal_str_list(victory_list)
        couple_id_list = self.get_couple_player_id_list()
        cupid_str = " x ".join(f"<@{player_id}>" for player_id in couple_id_list)

        couple_reveal_text = "\n\n" + "💘 " + cupid_str if couple_id_list else ""
        await self.interface.send_text_to_channel(
            "\n".join(reveal_str_list) + couple_reveal_text,
            config.GAMEPLAY_CHANNEL
        )

        # write to leaderboard
        if self.start_time is not None:  # game has been started
            await self.handle_end_game_score_list(game_winner, victory_list)
            game_result = text_templates.generate_embed(
                "game_result_embed",
                [
                    [str(self.day)],
                    # \u00A0\u00A0 is one space character for discord embed
                    # Put \u200B\n at first of the next field to break line
                    [f"🎉\u00A0\u00A0\u00A0\u00A0{game_winner}\u00A0\u00A0\u00A0\u00A0🎉"],
                    reveal_str_list,
                    [cupid_str] if couple_id_list else []
                ],
                start_time_str=self.start_time.strftime(text_templates.get_format_string("datetime")),
                total_players=len(self.players)
            )
            await self.interface.send_embed_to_channel(game_result, config.LEADERBOARD_CHANNEL)

        await self.cancel_running_task(self.task_run_timer_phase)
        print("End game loop")

    def get_winning_role(self):
        alives = self.get_alive_players()
        num_players = len(alives)
        num_werewolf = sum(Game.is_role_in_werewolf_party(p) for p in alives)

        print("DEBUG: ", num_players, num_werewolf)

        # Check Tanner
        tanner_id = self.get_player_with_role(roles.Tanner, 'all')
        if tanner_id:
            if self.players[tanner_id].is_lynched and self.players[tanner_id].get_party() == 'Tanner':
                return roles.Tanner

        # Check end game
        if num_werewolf != 0 and num_werewolf * 2 < num_players:
            return None

        # Check Cupid
        couple = [self.players[i] for i in self.get_couple_player_id_list()]
        if num_players == 2 and len(couple) > 0 and all(p.is_alive() for p in couple) and \
                all(Game.is_role_in_werewolf_party(p) != Game.is_role_in_werewolf_party(self.players[p.get_lover()]) for p in couple):
            return roles.Cupid

        # Werewolf still alive then werewolf win
        if num_werewolf != 0:
            return roles.Werewolf

        # Werewolf died and fox still alive
        if any(isinstance(p, roles.Fox) for p in alives):
            return roles.Fox

        return roles.Villager

    @staticmethod
    def get_top_voted(list_id):
        top_voted = Counter(list_id).most_common(2)
        print("get_top_voted", top_voted)
        if len(top_voted) == 1 or (len(top_voted) == 2 and top_voted[0][1] > top_voted[1][1]):
            return top_voted[0][0], top_voted[0][1]
        return None, 0  # have no vote or equal voted

    def get_voted_list(self, voter_dict):
        # self.voter_dict = {}  # Dict of voter:voted players {user1:user2, user3:user4, user2:user1}. All items are ids.
        voted_list = []
        for voter, voted in voter_dict.items():
            voted_list.append(voted)
            if isinstance(self.players[voter], roles.Chief):
                voted_list.append(voted)
            if isinstance(self.players[voter], roles.Tanner):
                self.players[voter].is_voted_other = True
        return voted_list

    async def control_muting_party_channel(self, channel_name, is_muted, player_list):
        """
        Mute/Unmute all alive players in party channel (e.g. GAMEPLAY_CHANNEL, WEREWOLF_CHANNEL, COUPLE_CHANNEL)
        """
        await asyncio.gather(*[
            self.interface.add_user_to_channel(_id, channel_name, is_read=True, is_send=not is_muted)
            for _id in player_list
            if self.players[_id].is_alive()
        ])

    async def do_new_daytime_phase(self):
        print("do_new_daytime_phase")
        self.day += 1

        if self.players:
            await asyncio.gather(*[
                player.on_day_start(self.day) for player in self.get_all_players()
            ])
            await self.interface.send_action_text_to_channel("day_phase_beginning_text", config.GAMEPLAY_CHANNEL, day=self.day)
            embed_data = self.generate_player_list_embed()
            await self.interface.send_embed_to_channel(embed_data, config.GAMEPLAY_CHANNEL)

            if self.new_moon_mode.is_on:
                self.new_moon_mode.set_random_event()
                _kwargs = {}
                if self.new_moon_mode.get_current_event() is Punishment and len(self.get_dead_players()):
                    alive_players_embed_data = self.generate_player_list_embed(True)
                    _kwargs = {"alive_players_embed_data": alive_players_embed_data}

                await self.new_moon_mode.do_new_daytime_phase(self.interface, **_kwargs)

            # Mute all party channels
            # Unmute all alive players in config.GAMEPLAY_CHANNEL
            await self.control_muting_party_channel(config.WEREWOLF_CHANNEL, True, self.get_werewolf_list())
            await self.control_muting_party_channel(config.COUPLE_CHANNEL, True, self.get_couple_player_id_list())
            await self.control_muting_party_channel(config.GAMEPLAY_CHANNEL, False, list(self.players.keys()))

            # init object
            self.voter_dict = {}
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
            lynched, votes = Game.get_top_voted(self.get_voted_list(self.voter_dict))
            print("lynched list:", self.voter_dict)
            self.voter_dict = {}

        if self.new_moon_mode.get_current_event() is HeadsOrTails:
            coin_toss_value = await self.new_moon_mode.do_end_daytime_phase(self.interface)
            if coin_toss_value != 0:
                lynched, votes = None, 0

        day_kill_list = []
        # Kill Tanner if they didn't vote anyone from the second to the sixth day
        tanner_id = self.get_player_with_role(roles.Tanner)
        if tanner_id and self.day >= 2:
            if not self.players[tanner_id].is_voted_other:
                # Tanner hasn't voted someone else and will be dead
                day_kill_list.append((tanner_id, const.DeadReason.TANNER_NO_VOTE))
                # Check if lynched player is also a Tanner
                if tanner_id == lynched:
                    lynched = None

        if lynched:
            if isinstance(self.players[lynched], roles.Tanner):
                self.players[lynched].is_lynched = True

            day_kill_list.append((lynched, const.DeadReason.LYNCHED))

        if day_kill_list:
            kills_list_by_reason = await self.get_final_status_changes_with_reasons(day_kill_list)
            await self.send_status_changes_info_on_end_phase(kills_list_by_reason, highest_vote_number=votes)

        if not lynched:
            await self.interface.send_action_text_to_channel("execution_none_text", config.GAMEPLAY_CHANNEL)

        players_embed_data = self.generate_player_list_embed()
        await self.interface.send_embed_to_channel(players_embed_data, config.GAMEPLAY_CHANNEL)

    async def do_new_nighttime_phase(self):
        print("do_new_nighttime_phase")
        if self.players:
            # Mute all players in config.GAMEPLAY_CHANNEL
            # Unmute all party channels
            await self.control_muting_party_channel(config.GAMEPLAY_CHANNEL, True, list(self.players.keys()))
            await self.control_muting_party_channel(config.WEREWOLF_CHANNEL, False, self.get_werewolf_list())
            await self.control_muting_party_channel(config.COUPLE_CHANNEL, False, self.get_couple_player_id_list())

            await self.interface.send_action_text_to_channel("night_phase_beginning_text", config.GAMEPLAY_CHANNEL)

            if self.new_moon_mode.is_on:
                await self.new_moon_mode.do_new_nighttime_phase(self.interface)

            # do on_night_start
            alive_embed_data = self.generate_player_list_embed(True)
            dead_embed_data = self.generate_player_list_embed(False)

            await self.werewolf_do_new_nighttime_phase(alive_embed_data)
            for player in self.get_alive_players():
                if isinstance(player, roles.ApprenticeSeer):
                    await self.apprenticeseer_do_new_nighttime_phase(player)

            await asyncio.gather(*[
                player.on_night_start(alive_embed_data, dead_embed_data) for player in self.get_all_players()
            ])

            # init object
            self.wolf_kill_dict = {}
            self.night_pending_kill_list = []
            self.reborn_set = set()

    async def werewolf_do_new_nighttime_phase(self, alive_embed_data):
        if self.new_moon_mode.get_current_event() is FullMoonVegetarian:
            return

        if self.is_werewolf_diseased:
            await self.interface.send_action_text_to_channel("werewolf_diseased_text", config.WEREWOLF_CHANNEL)
            return

        await self.interface.send_action_text_to_channel("werewolf_before_voting_text", config.WEREWOLF_CHANNEL)
        await self.interface.send_embed_to_channel(alive_embed_data, config.WEREWOLF_CHANNEL)

    async def apprenticeseer_do_new_nighttime_phase(self, author):
        seer_id = self.get_player_with_role(roles.Seer, "dead")
        active_status = seer_id is not None
        await author.set_active(active_status)

    async def do_end_nighttime_phase(self):
        # FIXME:
        # pylint: disable=too-many-branches
        await self.do_run_auto_hook()
        print("do_end_nighttime_phase")

        # TODO: move to Player class
        for player in self.get_alive_players():
            if isinstance(player, roles.Guard):
                await self.guard_do_end_nighttime_phase(player)

        for player in self.get_alive_players():
            if isinstance(player, roles.Seer):
                await self.seer_do_end_nighttime_phase(player)
            elif isinstance(player, roles.Witch):
                await self.witch_do_end_nighttime_phase(player)
            elif isinstance(player, roles.Pathologist):
                await self.pathologist_do_end_nighttime_phase(player)
            elif isinstance(player, roles.Rat):
                await self.rat_do_end_nighttime_phase(player)

        await self.werewolf_do_end_nighttime_phase()

        kills_list_by_reason = defaultdict(list)
        if self.night_pending_kill_list:
            kills_list_by_reason = await self.get_final_status_changes_with_reasons(self.night_pending_kill_list)
            self.night_pending_kill_list = []  # Reset killed list for next day

        # Morning deaths announcement
        if kills_list_by_reason:
            await self.send_status_changes_info_on_end_phase(kills_list_by_reason)
        else:
            await self.interface.send_action_text_to_channel("killed_none_text", config.GAMEPLAY_CHANNEL)

        if self.new_moon_mode.get_current_event() is TwinFlame and self.get_couple_player_id_list():
            await self.new_moon_mode.do_end_nighttime_phase(self.interface)

        reborn_list_by_reason = await self.get_final_status_changes_with_reasons(self.reborn_set)
        await self.send_status_changes_info_on_end_phase(reborn_list_by_reason)

        self.reborn_set = set()

    async def send_status_changes_info_on_end_phase(self, kills_list_by_reason, **kw_info):
        for reason, id_list in kills_list_by_reason.items():
            label = reason.get_template_label(self.game_phase)

            if reason is const.DeadReason.HIDDEN:
                await self.interface.send_action_text_to_channel(
                    label,
                    config.GAMEPLAY_CHANNEL,
                    user=", ".join(f"<@{_id}>" for _id in id_list)
                )
            else:
                for _id in id_list:
                    if reason is const.DeadReason.TANNER_NO_VOTE:
                        kwargs = {"user": f"<@{_id}>"}
                    elif reason is const.DeadReason.LYNCHED:
                        kwargs = {"voted_user": f"<@{_id}>", "highest_vote_number": kw_info.get("highest_vote_number", 0)}
                    elif reason is const.DeadReason.HUNTED:
                        kwargs = {"target": f"<@{_id}>"}
                    elif reason is const.DeadReason.COUPLE:
                        kwargs = {"died_player": f"<@{self.players[_id].get_lover()}>", "follow_player": f"<@{_id}>"}
                    elif reason is const.RebornReason.COUPLE:
                        lover_id = self.players[_id].get_lover()
                        await self.interface.add_user_to_channel(lover_id, config.COUPLE_CHANNEL, is_read=True, is_send=True)
                        await self.interface.add_user_to_channel(_id, config.COUPLE_CHANNEL, is_read=True, is_send=True)
                        kwargs = {"reborn_player": f"<@{lover_id}>", "follow_player": f"<@{_id}>"}
                    else:
                        continue

                    await self.interface.send_action_text_to_channel(label, config.GAMEPLAY_CHANNEL, **kwargs)

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
        if type(author) is roles.ApprenticeSeer and not author.is_active:
            return

        target_id = author.get_target()
        if target_id is None:
            return

        target = self.players[target_id]

        if roles.Seer.is_can_kill_fox() and isinstance(target, roles.Fox):
            self.night_pending_kill_list.append((target_id, const.DeadReason.HIDDEN))

        if self.new_moon_mode.get_current_event() is Somnambulism:
            await self.new_moon_mode.do_end_nighttime_phase(self.interface, target=target)

        await author.send_to_personal_channel(
            text_templates.generate_text(
                f"seer_result_{'' if target.seer_seen_as_werewolf() else 'not_'}werewolf_text",
                target=f"<@{target_id}>"
            )
        )

    async def pathologist_do_end_nighttime_phase(self, author):
        target_id = author.get_target()
        if target_id is None:
            return

        target = self.players[target_id]
        role = target.get_role()

        await author.send_to_personal_channel(
            text_templates.generate_text("pathologist_result_text", target=f"<@{target_id}>", role=role)
        )

    async def witch_do_end_nighttime_phase(self, author):
        reborn_target_id = author.get_reborn_target()
        if author.get_reborn_power() > 0 and reborn_target_id:
            author.on_use_reborn_power()
            self.reborn_set.add((reborn_target_id, const.RebornReason.HIDDEN))

            await author.send_to_personal_channel(
                text_templates.generate_text("witch_reborn_result_text", target=f"<@{reborn_target_id}>")
            )

        if roles.Witch.is_can_kill():
            curse_target_id = author.get_curse_target()
            if author.get_curse_power() > 0 and curse_target_id:
                author.on_use_curse_power()
                self.night_pending_kill_list.append((curse_target_id, const.DeadReason.HIDDEN))

                await author.send_to_personal_channel(
                    text_templates.generate_text("witch_curse_result_text", target=f"<@{curse_target_id}>")
                )

    async def rat_do_end_nighttime_phase(self, author):
        target_id = author.get_target()
        if target_id is None:
            return

        target = self.players[target_id]

        if isinstance(target, (roles.Fox, roles.Guard)):
            self.night_pending_kill_list.append((author.player_id, const.DeadReason.HIDDEN))
            await author.send_to_personal_channel(
                text_templates.generate_text("rat_dead_bite_text", target=f"<@{target_id}>")
            )
        else:
            self.night_pending_kill_list.append((target_id, const.DeadReason.HIDDEN))
            await author.send_to_personal_channel(
                text_templates.generate_text("rat_result_text", target=f"<@{target_id}>")
            )
            if isinstance(target, roles.Diseased):
                await self.do_diseased_effect(author.player_id)
                await author.send_to_personal_channel(
                    text_templates.generate_text("rat_diseased_bite_text", target=f"<@{target_id}>")
                )
                if not target.is_protected():
                    self.night_pending_kill_list.append((author.player_id, const.DeadReason.HIDDEN))

    async def werewolf_do_end_nighttime_phase(self):
        if self.is_werewolf_diseased:
            self.is_werewolf_diseased = False
            return

        if self.wolf_kill_dict:
            killed, _ = Game.get_top_voted(list(self.wolf_kill_dict.values()))
            print("killed", killed)
            if killed:
                self.night_pending_kill_list.append((killed, const.DeadReason.HIDDEN))
                await self.interface.send_action_text_to_channel(
                    "werewolf_kill_result_text", config.WEREWOLF_CHANNEL, target=f"<@{killed}>"
                )
                await self.do_werewolf_killed_effect(self.players[killed])

            self.wolf_kill_dict = {}

    async def do_werewolf_killed_effect(self, killed_player):
        if isinstance(killed_player, roles.Diseased):
            print("werewolf has been diseased")
            self.is_werewolf_diseased = True
            werewolf_list = self.get_werewolf_list()
            # affects all werewolves
            for werewolf_id in werewolf_list:
                await self.do_diseased_effect(werewolf_id)

    async def do_diseased_effect(self, target_id):
        target = self.players[target_id]
        target.add_next_disable_action_days(1)

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

        self.__is_on_phase = True

    async def end_phase(self):
        assert self.game_phase != const.GamePhase.NEW_GAME
        self.__is_on_phase = False
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

    async def do_player_action(self, cmd, author_id, *targets_id):
        # FIXME
        # pylint: disable=too-many-return-statements, too-many-branches
        if self.timer_enable and not self.__is_on_phase:
            return text_templates.generate_text(
                "not_in_phase_action_time_text",
                phase=text_templates.get_word_in_language(str(self.game_phase))
            )

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

        targets = []
        for target_id in targets_id:
            target = self.players.get(target_id)
            if target is None:
                return text_templates.generate_text("invalid_target_text")
            targets.append(target)

        if cmd == "zombie":
            return await self.zombie(author)

        is_alive_target_command = cmd not in ["reborn", "autopsy"]
        if is_alive_target_command != targets[0].is_alive():
            return text_templates.generate_text(
                "invalid_target_status_text",
                status=text_templates.get_word_in_language("alive" if is_alive_target_command else "dead")
            )

        if cmd in ("vote", "punish", "kill", "guard", "hunter", "seer", "reborn", "curse", "autopsy", "bite"):
            return await getattr(self, cmd)(author, targets[0])

        if cmd == "ship":
            if self.modes.get("couple_random", False):
                return text_templates.generate_text("invalid_ship_with_random_couple_text")
            return await self.ship(author, targets[0], targets[1])

        return text_template.generate_invalid_command_text(cmd)

    async def undo_player_action(self, author_id, channel_name):
        if self.game_phase == const.GamePhase.DAY:
            return await self.__undo_player_daytime_action(author_id, channel_name)

        if self.game_phase == const.GamePhase.NIGHT:
            return await self.__undo_player_nighttime_action(author_id, channel_name)

        return text_templates.generate_text("undo_command_failed_text", player=f"<@{author_id}>")

    async def __undo_player_daytime_action(self, author_id, channel_name):
        # vote, punish
        if channel_name in (config.GAMEPLAY_CHANNEL, config.CEMETERY_CHANNEL) and author_id in self.voter_dict:
            del self.voter_dict[author_id]
            if channel_name == config.CEMETERY_CHANNEL:
                await self.interface.send_action_text_to_channel(
                    "new_moon_punishment_undo_text", config.GAMEPLAY_CHANNEL, author=f"<@{author_id}>"
                )
            return text_templates.generate_text("undo_command_successful_text", player=f"<@{author_id}>")

        return text_templates.generate_text("undo_command_failed_text", player=f"<@{author_id}>")

    async def __undo_player_nighttime_action(self, author_id, channel_name):
        player = self.players[author_id]
        is_personal_channel = channel_name.startswith(config.PERSONAL)
        # kill
        if channel_name == config.WEREWOLF_CHANNEL and isinstance(player, roles.Werewolf) and author_id in self.wolf_kill_dict:
            del self.wolf_kill_dict[author_id]
            return text_templates.generate_text("undo_command_successful_text", player=f"<@{author_id}>")
        # guard, hunter, seer, autospy, bite
        if is_personal_channel and isinstance(player, (roles.Guard, roles.Hunter, roles.Seer, roles.ApprenticeSeer, roles.Pathologist, roles.Rat)) and player.get_target() is not None:
            player.set_target(None)
            return text_templates.generate_text("undo_command_successful_text", player=f"<@{author_id}>")
        # Undo curse, reborn just when Witch did any of them previously
        if is_personal_channel and isinstance(player, roles.Witch):
            witch_commands = ["curse", "reborn"]
            for command in witch_commands[:]:
                if getattr(player, f"get_{command}_power")() == 1 and getattr(player, f"get_{command}_target")() is not None:
                    getattr(player, f"set_{command}_target")(None)
                else:
                    witch_commands.remove(command)
            if len(witch_commands) > 0:
                return text_templates.generate_text("undo_witch_command_successful_text", commands=", ".join(witch_commands), player=f"<@{author_id}>")

        return text_templates.generate_text("undo_command_failed_text", player=f"<@{author_id}>")

    @command_verify_phase(const.GamePhase.DAY)
    async def vote(self, author, target):
        author_id = author.player_id
        target_id = target.player_id
        if author_id == target_id:
            return text_templates.generate_text("prevent_self_voting_text")

        # Vote for target user
        self.voter_dict[author_id] = target_id
        return text_templates.generate_text("vote_text", author=f"<@{author_id}>", target=f"<@{target_id}>")

    @NewMoonMode.active_in_event(Punishment, const.GamePhase.DAY)
    async def punish(self, author, target):
        author_id = author.player_id
        target_id = target.player_id

        # Punish for target user
        self.voter_dict[author_id] = target_id

        return await self.new_moon_mode.do_action(self.interface, author=f"<@{author_id}>", target=f"<@{target_id}>")

    @command_verify_author(roles.Werewolf)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def kill(self, author, target):
        if self.new_moon_mode.get_current_event() is FullMoonVegetarian:
            return await self.new_moon_mode.do_action(self.interface)

        author_id = author.player_id
        target_id = target.player_id

        self.wolf_kill_dict[author_id] = target_id
        return text_templates.generate_text("werewolf_after_voting_text", werewolf=f"<@{author_id}>", target=f"<@{target_id}>")

    @command_verify_author(roles.Guard)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def guard(self, author, target):
        roles.Guard.set_allow_self_protection(self.modes.get("allow_guard_self_protection", False))
        return author.register_target(target.player_id)

    @command_verify_author(roles.Seer)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def seer(self, author, target):
        return author.register_target(target.player_id)

    @command_verify_author(roles.Pathologist)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def autopsy(self, author, target):
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
        self.reborn_set.add((author_id, const.RebornReason.HIDDEN))

        return text_templates.generate_text("zombie_after_reborn_text")

    @command_verify_author(roles.Cupid)
    async def ship(self, author, target1, target2):
        if author is not None:  # quick adapt couple_random enable
            if author.get_power() == 0:
                return text_templates.generate_text("out_of_power_text")

            author.on_use_power()

        target1_id = target1.player_id
        target2_id = target2.player_id

        await self.interface.create_channel(config.COUPLE_CHANNEL)
        await target1.register_lover(target2.player_id, target2.get_role())
        await target2.register_lover(target1.player_id, target1.get_role())
        await self.interface.send_action_text_to_channel("couple_welcome_text", config.COUPLE_CHANNEL, user1=f"<@{target1_id}>", user2=f"<@{target2_id}>")

        return text_templates.generate_text("cupid_after_ship_text", target1=f"<@{target1_id}>", target2=f"<@{target2_id}>")

    @command_verify_author(roles.Hunter)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def hunter(self, author, target):
        return author.register_target(target.player_id)

    @command_verify_author(roles.Rat)
    @command_verify_phase(const.GamePhase.NIGHT)
    async def bite(self, author, target):
        return author.register_target(target.player_id)

    @staticmethod
    def is_role_in_werewolf_party(player):
        return isinstance(player, (roles.Werewolf, roles.Rat))

    def get_werewolf_list(self):
        werewolf_list = []
        for _id, player in self.players.items():
            if isinstance(player, roles.Werewolf):
                werewolf_list.append(_id)

        return werewolf_list

    def get_couple_player_id_list(self):
        return [_id for _id, player in self.players.items() if player.get_lover() is not None]

    def get_player_with_role(self, role, status='alive'):
        if status == 'alive':
            players = self.get_alive_players()
        elif status == 'dead':
            players = self.get_dead_players()
        else:
            players = self.get_all_players()

        for player in players:
            if type(player) is role:  # pylint: disable=unidiomatic-typecheck
                player_id = player.player_id
                return player_id
        return None

    async def register_auto(self, author_id, subcmd):
        assert self.players is not None
        # print(self.players)
        author = self.players.get(author_id)
        if author is None:
            return text_templates.generate_text("invalid_author_text")

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

        def has_no_target():
            return author.target is None

        @check(is_alive)
        @check(is_night)
        @check(has_role(roles.Guard))
        @check(has_no_target)
        async def auto_guard():
            target = random.choice(self.get_alive_players())
            msg = await self.guard(author, target)
            await author.send_to_personal_channel("[Auto] " + msg)

        @check(is_alive)
        @check(is_night)
        @check(has_role(roles.Seer))
        @check(has_no_target)
        async def auto_seer():
            target = random.choice(self.get_alive_players())
            if isinstance(author, roles.ApprenticeSeer) and not author.is_active:
                return

            if author.get_lover():
                while target.get_lover() == author.player_id:
                    target = random.choice(self.get_alive_players())
            msg = await self.seer(author, target)
            await author.send_to_personal_channel("[Auto] " + msg)

        @check(is_alive)
        @check(is_night)
        @check(has_role(roles.Pathologist))
        @check(has_no_target)
        async def auto_autopsy():
            if not self.get_dead_players():
                return

            target = random.choice(self.get_dead_players())
            if author.get_lover():
                while target.get_lover() == author.player_id:
                    target = random.choice(self.get_dead_players())
            msg = await self.autopsy(author, target)
            await author.send_to_personal_channel("[Auto] " + msg)

        if subcmd == "off":
            self.auto_hook[author] = []
            return "Clear auto succeeded"

        map_cmd_role = {
            "seer": (roles.Seer, auto_seer),
            "guard": (roles.Guard, auto_guard),
            "autopsy": (roles.Pathologist, auto_autopsy),
        }
        if subcmd in map_cmd_role:
            valid_role, auto_func = map_cmd_role[subcmd]
            if has_role(valid_role)():
                self.auto_hook[author].append(auto_func)
                return f"Register auto {subcmd} success"
            return f"You are not a {valid_role.__name__}"

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
