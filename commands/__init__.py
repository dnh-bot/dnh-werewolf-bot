"""Add cmd decorator here for parsing command parameters"""

import config
from config import BOT_PREFIX, TEXT_LANGUAGE
import utils
import text_templates
from game.const import CommandType, ChannelType

command_info = utils.common.read_json_file("json/command_info.json")


def get_all_commands():
    return [*command_info.keys()]


def get_all_commands_with_type():
    commands_filter_by_type = {}
    for command, command_dict in command_info.items():
        command_type = CommandType[command_dict["type"]]
        if command_type not in commands_filter_by_type:
            commands_filter_by_type[command_type] = []

        commands_filter_by_type[command_type].append(command)

    return sorted(commands_filter_by_type.items())


def get_command_description(command):
    if command in command_info:
        return command_info[command]["description"][TEXT_LANGUAGE]

    return None


def get_command_type(command):
    try:
        return CommandType[command_info[command]["type"]]
    except KeyError:
        return CommandType.PUBLIC


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


def get_command_examples_argv_list(command):
    if command in command_info:
        return command_info[command].get("examples", [])

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


def get_command_examples(command):
    required_params = get_command_required_params(command)
    additional_params = get_command_additional_params(command)
    params = required_params + additional_params

    example_args_list = get_command_examples_argv_list(command)
    return [
        example_text
        for example_args in example_args_list
        for example_text in get_command_usages(
            command, **dict(zip(params, example_args + [""] * len(additional_params)))
        )
    ]


def get_command_usages_str(cmd, **kwargs):
    return f' {text_templates.get_word_in_language("or")} '.join(get_command_usages(cmd, **kwargs))


def get_command_examples_str(cmd):
    return f' {text_templates.get_word_in_language("or")} '.join(get_command_examples(cmd))


def get_channel_type(channel_name):
    if channel_name.startswith(config.PERSONAL):
        return ChannelType.PERSONAL
    if channel_name == config.WEREWOLF_CHANNEL:
        return ChannelType.WEREWOLF
    if channel_name == config.LOBBY_CHANNEL:
        return ChannelType.LOBBY
    if channel_name == config.GAMEPLAY_CHANNEL:
        return ChannelType.GAMEPLAY

    return ChannelType.PUBLIC


def is_command_in_valid_channel(command, channel_name):
    return get_command_type(command) == CommandType.PUBLIC \
        or get_command_type(command) == get_channel_type(channel_name)


def get_command_valid_channels(command):
    command_type = get_command_type(command)
    if command_type == CommandType.PERSONAL:
        return [text_templates.get_word_in_language("personal")]
    if command_type == CommandType.WEREWOLF:
        return [config.WEREWOLF_CHANNEL]
    if command_type == ChannelType.LOBBY:
        return [config.LOBBY_CHANNEL]
    if command_type == ChannelType.GAMEPLAY:
        return [config.GAMEPLAY_CHANNEL]

    return []  # public channels


def get_command_valid_channel_name(command):
    valid_channels = get_command_valid_channels(command)
    return f' {text_templates.get_word_in_language("or")} '.join(valid_channels)
