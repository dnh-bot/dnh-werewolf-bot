from typing import List

from config import BOT_PREFIX, TEXT_LANGUAGE
import utils

text_template_dict = utils.common.read_json_file("json/text_template.json")


def get_all_objects():
    return text_template_dict


def get_text_object(action):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return template_obj

    return {}


def get_template_params(action):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return template_obj["params"]

    return []


def get_word_in_language(key):
    if key in text_template_dict["KEYWORDS"]:
        return text_template_dict["KEYWORDS"][key][TEXT_LANGUAGE]

    return ""


def get_label_in_language(key):
    if key in text_template_dict["LABEL"]:
        return text_template_dict["LABEL"][key][TEXT_LANGUAGE]

    return ""


def get_format_string(key):
    if key in text_template_dict["FORMAT_STRING"]:
        return text_template_dict["FORMAT_STRING"][key][TEXT_LANGUAGE]

    return ""


def generate_text_list(action, **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return [
            line.format(
                bot_prefix=BOT_PREFIX, **kwargs
            )
            for line in template_obj["template"][TEXT_LANGUAGE]
        ]

    print(f"Error in generate_text_list: action={action} not in text_template.json")
    return ""


def generate_text(action, **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return "\n".join(template_obj["template"][TEXT_LANGUAGE]).format(
            bot_prefix=BOT_PREFIX, **kwargs
        ).rstrip()

    print(f"Error in generate_text: action={action} not in text_template.json")
    return ""


def generate_table_headers(action, **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return [
            header.format(bot_prefix=BOT_PREFIX, **kwargs)
            for header in template_obj["template"][TEXT_LANGUAGE]
        ]

    return []


def generate_embed(action, content_values: List[List[str]], **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        embed_template = template_obj["template"][TEXT_LANGUAGE]
        return {
            "color": int(template_obj.get("color") or "0xffffff", 16),
            "title": embed_template["title"].format(bot_prefix=BOT_PREFIX, **kwargs),
            "description": embed_template["description"].format(bot_prefix=BOT_PREFIX, **kwargs),
            "content": [
                (
                    header.format(bot_prefix=BOT_PREFIX, **kwargs),
                    [line.format(bot_prefix=BOT_PREFIX, **kwargs) for line in value if line]
                )
                for header, value in zip(embed_template["content_headers"], content_values)
                if header and value
            ]
        }

    print(f"Error in generate_embed: action={action} not in text_template.json")
    return None
