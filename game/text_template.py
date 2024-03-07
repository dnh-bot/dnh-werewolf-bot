from game import roles
from game.roles.character import CharacterStatus
import text_templates
import commands

from datetime import *
from dateutil import parser, tz
from config import TEXT_LANGUAGE


def get_full_cmd_description(cmd):
    description = commands.get_command_description(cmd)
    usage_text = f" {text_templates.get_word_in_language('or')} ".join(commands.get_command_usages(cmd))
    return f"{description} {text_templates.get_word_in_language('use_command')} {usage_text}."


def generate_player_list_embed(player_list, alive_status=None, role_list=None):
    # Handle 3 types of list: Alive, Dead, Overview
    if player_list:
        id_player_list = generate_id_player_list(player_list, alive_status)
        action_name = f"{'all' if alive_status is None else 'alive' if alive_status else 'dead'}_player_list_embed"
        embed_data = text_templates.generate_embed(action_name, [id_player_list] if role_list is None else [id_player_list, role_list])
        return embed_data
    return None


def generate_id_player_list(player_list, alive_status):
    id_player_list = []
    row_id = 1
    for user in player_list:
        if alive_status is None and user.status == CharacterStatus.KILLED:
            id_player_list.append(f"💀 -> <@{user.player_id}>") # Do not increase row_id when user is dead
        else:
            id_player_list.append(f"{row_id} -> <@{user.player_id}>")
            row_id += 1

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
                voters_str=', '.join(f'<@!{_id}>' for _id in sorted(votes))
            )
            for vote_title, votes in sorted(vote_table.items(), key=lambda t: (-len(t[1]), t[0]))
            if len(votes)
        ]
        if vote_field:
            return vote_field
        else:
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
        help_embed_data = text_templates.generate_embed("help_command_all_embed", [])
        help_embed_data["content"] = [(cmd, [commands.get_command_description(cmd)]) for cmd in all_commands]

    elif command in all_commands:
        command_description = commands.get_command_description(command)
        command_exclusive_roles = commands.get_command_exclusive_roles(command)
        if len(command_exclusive_roles) > 0:
            command_exclusive_roles_str = ", ".join(command_exclusive_roles)
        else:
            command_exclusive_roles_str = text_templates.get_word_in_language("everyone")

        usage_str = ["- " + usage_text for usage_text in commands.get_command_usages(command)]

        if command in ("vote", "kill", "guard", "seer", "reborn", "curse"):
            example_args_list = [{"player_id": 2}]
        elif command == "ship":
            example_args_list = [{"player_id1": 2, "player_id2": 3}]
        elif command == "timer":
            example_args_list = [{"dayphase": 60, "nightphase": 30, "alertperiod": 20}]
        elif command == "setmode":
            example_args_list = [{"mode_id": "2", "on_str": "on"}]
        elif command == "setplaytime":
            example_args_list = [
                {"time_start": "00:00", "time_end": "23:59", "time_zone": ""},
                {"time_start": "00:00", "time_end": "23:59", "time_zone": "UTC+7"}
            ]
        else:
            example_args_list = []

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
    all_roles_name = [a_role.__name__ for a_role in roles.get_all_roles()]
    role = role.capitalize() if isinstance(role, str) else role
    if role is None:
        help_embed_data = text_templates.generate_embed("help_role_all_embed", [])
        help_embed_data["content"] = [
            (roles.get_role_title(role_name), [roles.get_role_description(role_name)])
            for role_name in all_roles_name
        ]

    elif role in all_roles_name:
        nighttime_commands = roles.get_role_nighttime_commands(role)
        if nighttime_commands:
            nighttime_actions_description = ["- " + get_full_cmd_description(cmd) for cmd in nighttime_commands]
        else:
            nighttime_actions_description = [text_templates.generate_text("nighttime_no_actions_text")]

        help_embed_data = text_templates.generate_embed(
            "help_role_embed", [[get_full_cmd_description("vote")], nighttime_actions_description],
            role_title=roles.get_role_title(role), role_description=roles.get_role_description(role)
        )
    else:
        help_embed_data = text_templates.generate_embed("help_invalid_name_embed", [], arg_type="role", arg_name=role)

    return help_embed_data


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


def generate_table(header, data):
    # This needs to be adjusted based on expected range of values or calculated dynamically
    # header + ["   ".join(str(item) for item in data] * len(data)

    # Joining up scores into a line
    return "```"+"\n".join(header + ["   ".join(str(item) for item in data)] * len(data)) + "```"


def generate_modes(modes_dict):
    print(modes_dict)
    mode_list = text_templates.get_text_object("mode_list_text")["template"][TEXT_LANGUAGE]

    return "===========================================================================\n" +\
        f"{mode_list['title']}: \n" +\
        "".join(
            f"- {i}. {title}: {'`ON`' if modes_dict.get(mode, None) == 'True' else '`OFF`' if modes_dict.get(mode, None) == 'False' else '`NONE`'}\n"
            for i, (mode, title) in enumerate(mode_list.items(), 0) if mode != 'title'
        ) +\
        "===========================================================================\n"


def generate_reveal_str_list(reveal_list, game_winner, cupid_dict):
    winner_list = generate_winner_list(reveal_list, game_winner, cupid_dict)

    return [
        "- " + text_templates.generate_text("reveal_player_text", player_id=player_id, role=role, result_emoji=result_emoji)
        for player_id, role, result_emoji in winner_list
    ]


def generate_winner_list(reveal_list, game_winner, cupid_dict):
    winner_list = []
    for player_id, role in reveal_list:
        party_victory = roles.get_role_party(role) == game_winner
        cupid_victory = game_winner == 'Cupid' and player_id in cupid_dict

        if party_victory or cupid_victory:
            emoji = '🥳'
        else:
            emoji = '😭'

        winner_list.append((player_id, role, emoji))

    return winner_list


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
    else:
        return text_templates.generate_text(
            "play_time_without_utc_text",
            time_range_str=time_range_str
        )
