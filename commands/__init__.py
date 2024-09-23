"""Add cmd decorator here for parsing command parameters"""

from collections import defaultdict

import config
from config import BOT_PREFIX, TEXT_LANGUAGE
import utils
import text_templates

command_info = utils.common.read_json_file("json/command_info.json")


def get_all_commands():
    return [*command_info.keys()]


def get_commands_by_type_list():
    type_commands_list = defaultdict(list)
    for command, data in command_info.items():
        type_commands_list[data["type"]].append(command)

    return type_commands_list


def get_command_description(command):
    if command in command_info:
        return command_info[command]["description"][TEXT_LANGUAGE]

    return None


def get_command_valid_channels(command):
    if command in command_info:
        return command_info[command].get("valid_channels", [])

    return []


def get_command_exclusive_roles(command):
    if command in command_info:
        return command_info[command]["exclusive_roles"]

    return None


def get_command_required_params(command):
    if command in command_info:
        return command_info[command]["required_params"]

    return []


def get_command_additional_params(command):
    if command in command_info:
        return command_info[command].get("additional_params", [])

    return []


def get_command_usages(command, **kwargs):
    if command in (config.ADMIN_CMD_PREFIX + "join", config.ADMIN_CMD_PREFIX + "leave"):
        return [f"`{BOT_PREFIX}{command} @user1 @user2 ...`"]

    if command in command_info:
        required_params = get_command_required_params(command)
        additional_params = get_command_additional_params(command)

        command_args_list = []
        command_args = []
        command_args_2 = []

        for param in required_params:
            argv = str(kwargs.get(param, param))
            if argv:
                command_args.append(argv)
                command_args_2.append(f"@user{param[9:]}" if param.startswith("player_id") else argv)

        for param in additional_params:
            argv = str(kwargs.get(param, "[" + param + "]"))
            if argv:
                command_args.append(argv)
                command_args_2.append(f"@user{param[9:]}" if param.startswith("player_id") else argv)

        command_args_list.append(command_args)
        if command_args != command_args_2:
            command_args_list.append(command_args_2)

        # print(command, required_params, additional_params, kwargs, "->", *command_args_list)

        return [
            f"`{' '.join([f'{BOT_PREFIX}{command}'] + command_args)}`"
            for command_args in command_args_list
        ]

    return []


def is_command_in_valid_channel(command, channel_name):
    valid_channels = get_command_valid_channels(command)
    if not valid_channels:
        return True

    return any(
        channel_name.strip().startswith("personal") if valid_channel_name == "PERSONAL" else
        channel_name == getattr(config, f"{valid_channel_name}_CHANNEL", "")
        for valid_channel_name in valid_channels
    )
