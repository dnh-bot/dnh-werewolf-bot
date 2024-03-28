from config import TEXT_LANGUAGE
import utils
import text_templates

mode_info = utils.common.read_json_file("json/mode_info.json")


def get_mode_title(key):
    if key in mode_info:
        return mode_info[key]["title"][TEXT_LANGUAGE]

    return key


def generate_on_off_value(str_value):
    if str_value in ["True", "on"]:
        return text_templates.get_word_in_language("turn_on").capitalize()

    if str_value in ["False", "off"]:
        return text_templates.get_word_in_language("turn_off").capitalize()

    return "None"


def generate_modes_text(modes_dict):
    print(modes_dict)

    return "===========================================================================\n" +\
        f"{text_templates.generate_text('show_modes_title')}: \n" +\
        "".join(
            f"- {i}. {get_mode_title(mode_str)}: `{generate_on_off_value(modes_dict.get(mode_str))}`\n"
            for i, mode_str in enumerate(modes_dict.keys(), 1)
        ) +\
        "===========================================================================\n"
