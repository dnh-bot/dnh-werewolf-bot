from typing import List

from config import BOT_PREFIX, TEXT_LANGUAGE, GAMEPLAY_CHANNEL
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
    return text_template_dict["KEYWORDS"][key][TEXT_LANGUAGE]


def generate_text(action, **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        return "\n".join(template_obj["template"][TEXT_LANGUAGE]).format(bot_prefix=BOT_PREFIX, gameplay_channel=GAMEPLAY_CHANNEL, **kwargs).rstrip()

    return ""


def generate_embed(action, content_values: List[List[str]], **kwargs):
    if action in text_template_dict:
        template_obj = text_template_dict[action]
        embed_template = template_obj["template"][TEXT_LANGUAGE]
        return {
            "color": int(template_obj.get("color") or "0xffffff", 16),
            "title": embed_template["title"].format(bot_prefix=BOT_PREFIX, **kwargs),
            "description": embed_template["description"].format(bot_prefix=BOT_PREFIX, **kwargs),
            "content": [
                (header, [line.format(bot_prefix=BOT_PREFIX, **kwargs) for line in value])
                for header, value in zip(embed_template["content_headers"], content_values)
                if value
            ]
        }

    return None
