from datetime import *

from dateutil import parser, tz

from game import roles
from game.roles.character import CharacterStatus
import text_templates
import commands


def get_full_cmd_description(cmd):
    description = commands.get_command_description(cmd)
    usage_text = f" {text_templates.get_word_in_language('or')} ".join(commands.get_command_usages(cmd))
    return f"{description} {text_templates.get_word_in_language('use_command')} {usage_text}."


def generate_player_score_list_embed(player_score_data):
    num_of_players = 10
    if player_score_data:
        sorted_player_score_data = sorted(player_score_data.items(), key=lambda x: x[1], reverse=True)[:num_of_players]
        player_score_list = [f"{i+1}. <@{player_id}> -> **{score}**" for i, (player_id, score) in enumerate(sorted_player_score_data)]
        god_of_war_list = [f"⚔️ <@{player_id}>" for i, (player_id, _) in enumerate(sorted_player_score_data) if (i+1) <= 3]
        embed_data = text_templates.generate_embed("player_score_list_embed", [player_score_list, god_of_war_list], num_of_players=num_of_players)
        return embed_data
    return None


def generate_id_player_list(player_list, alive_status, reveal_role=False):
    id_player_list = []
    row_id = 1
    for user in player_list:
        if alive_status is None and user.status == CharacterStatus.KILLED:
            # Handle for dead players in All list
            # Do not increase row_id when user is dead
            id_str = '💀'
        else:
            # Show player id for: alive players in All list, Alive list; dead players in Dead list.
            id_str = str(row_id)
            row_id += 1

        # Show role info if user is dead and reveal mode is enabled.
        dead_player_role_str = f" - ***{user.get_role()}***" if reveal_role and user.status == CharacterStatus.KILLED else ""
        id_player_list.append(f"{id_str} -> <@{user.player_id}>{dead_player_role_str}")

    return id_player_list


def generate_vote_field(vote_table):
    # vote_table format: {"u2": {"u1"}, "u1": {"u3", "u2"}}
    # ->
    # - @user1: 2 phiếu (@user2, @user3)
    # - @user2: 1 phiếu (@user1)

    if isinstance(vote_table, dict):
        vote_field = [
            text_templates.generate_text(
                "game_status_vote_field_text",
                be_voted_str=vote_title,
                votes_num=len(votes),
                voters_str=', '.join(f'<@{_id}>' for _id in sorted(votes))
            )
            for vote_title, votes in sorted(vote_table.items(), key=lambda t: (-len(t[1]), t[0]))
            if len(votes)
        ]
        if vote_field:
            return vote_field

        return [text_templates.generate_text("nobody_text")]

    return None


# Common
def generate_invalid_command_text(command):
    usage_list = ["- " + usage_text for usage_text in commands.get_command_usages(command)]
    return text_templates.generate_text(
        "invalid_command_text",
        command=command, text=("\nUsage:\n" + "\n".join(usage_list)) if usage_list else ""
    )


def generate_timer_remaining_text(seconds):
    if seconds is None:
        return ""

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_text = []
    if days > 0:
        time_text.append(text_templates.generate_text("count_days_text", days=days))
    if hours > 0:
        time_text.append(text_templates.generate_text("count_hours_text", hours=hours))
    if minutes > 0:
        time_text.append(text_templates.generate_text("count_minutes_text", minutes=minutes))
    if seconds > 0 or days == hours == minutes == seconds == 0:
        time_text.append(text_templates.generate_text("count_seconds_text", seconds=seconds))

    return " ".join(time_text)


def generate_help_command_embed(command=None):
    all_commands = commands.get_all_commands()
    command = command.lower() if isinstance(command, str) else command
    if command is None:
        type_commands_list = commands.get_commands_by_type_list()
        help_embed_data = text_templates.generate_embed(
            "help_command_all_embed",
            [[" | ".join(f"`{command}`" for command in type_commands_list[k])] for k in ("general", "game", "action")]
        )

    elif command in all_commands:
        command_description = commands.get_command_description(command)
        command_exclusive_roles = commands.get_command_exclusive_roles(command)
        if len(command_exclusive_roles) > 0:
            command_exclusive_roles_str = ", ".join(command_exclusive_roles)
        else:
            command_exclusive_roles_str = text_templates.get_word_in_language("everyone")

        usage_str = ["- " + usage_text for usage_text in commands.get_command_usages(command)]

        if command == "timer":
            example_args_list = [{"dayphase": 60, "nightphase": 30, "alertperiod": 20}]
        elif command == "setmode":
            example_args_list = [{"mode_id": "2", "on_str": "on"}]
        elif command == "setroles":
            example_args_list = [{"role_dict": '''[{{"Werewolf": 1, "Seer": 1, "Guard": 1, "Chief": 1, "Witch": 1}}]'''}]
        elif command == "setplaytime":
            example_args_list = [
                {"time_start": "00:00", "time_end": "23:59", "time_zone": ""},
                {"time_start": "00:00", "time_end": "23:59", "time_zone": "UTC+7"}
            ]
        elif command == "auto":
            example_args_list = [
                {"cmd": "seer"},
                {"cmd": "guard"},
                {"cmd": "autopsy"},
                {"cmd": "off"}
            ]
        else:
            example_args_list = [{"player_id": 2, "player_id1": 2, "player_id2": 3}]

        help_embed_data = text_templates.generate_embed(
            "help_command_embed", [
                [command_exclusive_roles_str],
                usage_str,
                [
                    "- " + example_text
                    for example_args in example_args_list
                    for example_text in commands.get_command_usages(command, **example_args)
                ]
            ],
            command=command, command_description=command_description
        )
    else:
        help_embed_data = text_templates.generate_embed(
            "help_invalid_name_embed", [],
            arg_type="command", arg_name=command
        )

    return help_embed_data


def generate_help_role_embed(role=None):
    if role is None:
        party_description_list = text_templates.generate_text_list("party_description_list")
        party_roles_list = roles.get_party_roles_list()
        help_embed_data = text_templates.generate_embed(
            "help_role_all_embed",
            [
                [party_description, *[f"- {role_title}" for role_title in role_list]]
                for party_description, role_list in zip(party_description_list, party_roles_list)
            ]
        )
        return help_embed_data

    role_data = roles.get_role_data_by_name(role)
    if not role_data:
        return text_templates.generate_embed("help_invalid_name_embed", [], arg_type="role", arg_name=role)

    party_name_list = text_templates.generate_text_list("party_name_list")

    title = role_data["title"]
    party = party_name_list[role_data["party"] - 1]
    description = role_data["description"]
    nighttime_commands = role_data["nighttime_commands"]
    if nighttime_commands:
        nighttime_actions_description = ["- " + get_full_cmd_description(cmd) for cmd in nighttime_commands]
    else:
        nighttime_actions_description = [text_templates.generate_text("nighttime_no_actions_text")]

    return text_templates.generate_embed(
        "help_role_embed", [[get_full_cmd_description("vote")], nighttime_actions_description],
        role_title=title, role_party=party, role_description=description
    )


def generate_help_embed(*args):
    if len(args) == 0:
        help_embed_data = text_templates.generate_embed("help_embed", [
            [" | ".join(f"`{cmd}`" for cmd in commands.get_all_commands())],
            [" | ".join(f"`{a_role.__name__}`" for a_role in roles.get_all_roles())]
        ])
    elif args[0] == "role":
        help_embed_data = generate_help_role_embed(None if len(args) == 1 else args[1])
    elif args[0] == "cmd":
        help_embed_data = generate_help_command_embed(None if len(args) == 1 else args[1])
    else:
        help_embed_data = text_templates.generate_embed("help_invalid_embed", [], args=args[0])

    return help_embed_data


def generate_reveal_str_list(victory_list=None):
    if victory_list is None:
        return ""

    return [
        "- " + text_templates.generate_text(
            "reveal_player_text", player_id=player_id, role=role, result_emoji='🥳' if victory else '😭'
        )
        for player_id, role, victory in victory_list
    ]


def time_range_to_string(start_time, end_time, zone):
    if start_time == end_time:
        template_name = "time_range_whole_day_text"
    elif str(end_time) == "00:00:00":
        template_name = "time_range_end_of_day_text"
    elif start_time < end_time:
        template_name = "time_range_start_le_end_text"
    else:
        template_name = "time_range_start_ge_end_text"

    return text_templates.generate_text(template_name, start_time=start_time, end_time=end_time, zone=zone)


def generate_play_time_text(start_time_utc: datetime.time, end_time_utc: datetime.time, zone_str=""):
    start_time_utc = parser.parse(f"{start_time_utc} {zone_str}")
    end_time_utc = parser.parse(f"{end_time_utc} {zone_str}")

    # Convert time zone
    to_zone = tz.gettz(zone_str) if zone_str else tz.gettz()
    start_time = start_time_utc.replace(tzinfo=tz.UTC).astimezone(to_zone)
    end_time = end_time_utc.replace(tzinfo=tz.UTC).astimezone(to_zone)

    zone = zone_str or str(to_zone.tzname(None))
    time_range_str = time_range_to_string(start_time.time(), end_time.time(), zone)
    if start_time_utc != start_time != end_time:
        # zone is not UTC and the play time is not a whole day
        return text_templates.generate_text(
            "play_time_with_utc_text",
            time_range_str=time_range_str,
            utc_time_range_str=time_range_to_string(start_time_utc.time(), end_time_utc.time(), 'UTC')
        )

    return text_templates.generate_text(
        "play_time_without_utc_text",
        time_range_str=time_range_str
    )
