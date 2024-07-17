import random

import text_templates
from config import GAMEPLAY_CHANNEL
from game.modes.new_moon.events.base import NewMoonEvent


class HeadsOrTails(NewMoonEvent):
    KEY = "heads_or_tails"

    @classmethod
    async def on_day_end(cls, interface, **kwargs):
        coin_toss_value = random.randint(0, 1)
        print("toss a coin -> coin toss value =", coin_toss_value)

        if coin_toss_value != 0:
            coin_value_str = text_templates.get_word_in_language("coin_head")
        else:
            coin_value_str = text_templates.get_word_in_language("coin_tail")

        await cls.send_result_text(interface, GAMEPLAY_CHANNEL, coin_value_str=coin_value_str)
        return coin_toss_value
