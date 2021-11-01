"""Add cmd decorator here for parsing command parameters"""

from config import TEXT_LANGUAGE
import utils

command_info = utils.common.read_json_file("json/command_info.json")


def get_all_commands():
    return [*command_info.keys()]


def get_command_description(command):
    # TODO: command == status: description = Show status of current phase.
    if command in command_info:
        return command_info[command]["description"][TEXT_LANGUAGE]

    return None


def get_command_param_number(command):
    if command in command_info:
        return command_info[command]["required_param_number"]

    return None
