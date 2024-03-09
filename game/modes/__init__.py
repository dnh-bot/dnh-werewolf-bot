import random
from typing import List

from config import BOT_PREFIX, TEXT_LANGUAGE, GAMEPLAY_CHANNEL
import utils

mode_info_dict = utils.common.read_json_file("json/mode_info.json")
