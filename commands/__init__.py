"""Add cmd decorator here for parsing command parameters"""
import json

from config import TEXT_LANGUAGE

COMMAND_INFO_FILE = "json/command_info.json"


def read_command_info_json():
    try:
        with open(COMMAND_INFO_FILE, "r", encoding="utf8") as f:
            print(f"successfully loaded {COMMAND_INFO_FILE}")
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


command_info = read_command_info_json()


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
